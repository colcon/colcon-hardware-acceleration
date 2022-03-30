# Copyright 2022 Víctor Mayoral-Vilches
# Licensed under the Apache License, Version 2.0

import os
import sys

from colcon_core.package_discovery import discover_packages
from colcon_core.package_identification import get_package_identification_extensions
from colcon_core.plugin_system import satisfies_version
from colcon_hardware_acceleration.subverb import (
    AccelerationSubverbExtensionPoint,
    check_install_directory,
    get_rawimage_path,
    run,
    get_install_dir,
    get_firmware_dir,
    get_vitis_dir,
    get_vivado_dir,
    exists,
)
from colcon_hardware_acceleration.verb import (
    green,
    yellow,
    red,
    greeninline,
    redinline,
    yellowinline,
    grayinline,
    magenta,
    gray,
)


class HLSSubverb(AccelerationSubverbExtensionPoint):
    """Vitis HLS capabilities management extension.

    NOTE: Default behavior of this subverb is to show the HLS "status"

    Exposes Vitis HLS suite at the colcon meta build tools level for ROS 2 packages. Provides:
        0. Capability to show the HLS status of a given ROS 2 package
        1. Capability to launch Tcl scripts (pre-generated with ament macros, e.g. see vitis_hls_generate_tcl)
        2. Capability to bring up summarized versions of synthesis reports

    """

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(
            AccelerationSubverbExtensionPoint.EXTENSION_POINT_VERSION, "^1.0"
        )

    def add_arguments(self, *, parser):  # noqa: D102

        argument = parser.add_argument(
            "package_name",
            nargs="?",
            help="Name of the package whereto run HLS",
        )
        argument = parser.add_argument("--verbose", dest="verbose", action="store_true")
        argument = parser.add_argument("--summary", dest="summary", action="store_true")
        argument = parser.add_argument(
            "--run",
            dest="run",
            action="store_true",
            help="Run HLS from CLI according to the Tcl scripts",
        )
        argument = parser.add_argument(
            "--silent",
            dest="silent",
            action="store_true",
            help="Do not provide a summary for each solution",
        )
        argument = parser.add_argument(
            "--synthesis-report",
            dest="synthesis_report",
            action="store_true",
            help="Extend the status report for each solution with the synthesis report",
        )

    def find_tcl_package(self, package_name):
        """Find Tcl scripts for the package_name

        NOTE: silly filtering based on simply substring matching, consider
        more complex filtering with end-of-string if necessary in the future

        :param string package_name: ROS 2 package name whereto execute HLS
        :rtype list
        """
        current_dir = os.environ.get("PWD", "")
        filter_data = [
            x for x in os.listdir(current_dir) if all(y in x for y in ["build"])
        ]
        if len(filter_data) < 1:
            red(
                "No build* directories found.\n"
                + "Make sure you're in the root of your colcon workspace and the build "
                + "dir starts with 'build'."
            )
            sys.exit(1)

        package_paths = []  # paths under a build* dir that match with package_name
        package_paths_tcl = []  # above, and that contain a .tcl file
        for buildir in filter_data:
            build_current_dir = current_dir + "/" + buildir
            for x in os.listdir(build_current_dir):
                # if all(y in x for y in [package_name]):
                if x == package_name:
                    package_paths.append(build_current_dir + "/" + x)

        for p in package_paths:
            for x in os.listdir(p):
                if all(y in x for y in [".tcl"]):
                    package_paths_tcl.append(p + "/" + x)

        # drop any matches of .tcl.in as this is part of the ament generation process
        package_paths_tcl = [
            x for x in package_paths_tcl if all(y not in x for y in [".tcl.in"])
        ]

        return package_paths_tcl

    def process_tcl(self, tcl):
        """Process Tcl script and return a config dict

        NOTE: data structure of the return type is as follows:
            {
                'path': '<path-to-ros2-ws>/build-zcu102/simple_adder/project_simpleadder1',
                'project': 'project_simpleadder1',
                'solutions': [
                        {'solution_4ns': {
                                'clock': '4',
                                'path': '<path-to-ros2-ws>/build-zcu102/simple_adder/project_simpleadder1/solution_4ns'}
                        },
                        {'solution_10ns': {
                                'clock': '10',
                                'path': '<path-to-ros2-ws>/build-zcu102/simple_adder/project_simpleadder1/solution_10ns'}
                        }
                ]
            }

        :param string tcl: Tcl script path
        :rtype dict
        """
        tcl_dic = {}

        import re

        if not exists(tcl):
            red("Tcl " + tcl + " not found")
            sys.exit(1)

        data = open(tcl, "r").read()
        project = re.findall("open_project -reset (.*)", data)[0]
        solutions = re.findall("open_solution (.*)", data)
        clocks = re.findall("create_clock -period (.*)", data)
        parts = re.findall("set_part {(.*)}", data)
        path = re.findall("(.*)/.*$", tcl)[0] + "/" + project
        top = re.findall("set_top (.*)", data)[0]

        if len(solutions) != len(clocks) or len(solutions) != len(parts):
            red("Size mismatch between solutions, clocks and parts")
            sys.exit(1)

        # assign the dict
        tcl_dic["project"] = project
        tcl_dic["path"] = path
        tcl_dic["top"] = top
        tcl_dic["solutions"] = []
        for i in range(len(solutions)):
            solution = {
                solutions[i]
                .replace("-flow_target vitis", "")
                .strip(): {
                    "clock": clocks[i],
                    "path": path
                    + "/"
                    + solutions[i].replace("-flow_target vitis", "").strip(),
                }
            }
            tcl_dic["solutions"].append(solution)

        return tcl_dic

    def run_tcl(self, context, tcl):
        """Run Tcl script with vitis_hls

        :param string tcl: path to Tcl script
        :rtype: None
        """
        cmd = (
            "cd " + tcl[: tcl.rfind("/")] + " && vitis_hls -f " + tcl + " 2> /dev/null"
        )
        outs, errs = run(cmd, shell=True)
        if errs:
            red(errs)
            sys.exit(1)
        if context.args.verbose:
            print(outs)

    def print_status_solution(self, solution, configuration, context):
        """Print the status of a solution

        NOTE: Tested in Vitis 2020.2

        :param solution: solution to print with shape as in
                {'solution_4ns': {'clock': '4', 'path': '<path-to-ros2-ws>/build-zcu102/simple_adder/project_simpleadder1/solution_4ns'}}
        :param configuration: data structure with the configuration
        :rtype: None
        """
        solution_name = list(solution.keys())[0]
        solution_dict = solution[solution_name]
        grayinline("\t- Solution: ")
        magenta(solution_name)

        #######################
        # gather project status
        #######################
        project_status = []
        csimlog_path = (
            solution_dict["path"] + "/csim/report/" + configuration["top"] + "_csim.log"
        )
        try:
            with open(csimlog_path, "r") as f:
                # Pass/Fail info is always in the second last line of the csim report
                status_line = f.readlines()[-2]
                if "0 errors" in status_line.lower():
                    project_status.append("csim_pass")
                elif "fail" in status_line.lower():
                    project_status.append("csim_fail")
                else:
                    project_status.append("csim_done")
            f.close()
        except (OSError, IOError):
            pass

        # Pull setails from csynth report
        csyn_path = (
            solution_dict["path"]
            + "/syn/report/"
            + configuration["top"]
            + "_csynth.rpt"
        )
        if os.path.isfile(csyn_path):
            project_status.append("syn_done")

        # Pull details from cosim report
        try:
            cosim_path = (
                solution_dict["path"]
                + "/sim/report/"
                + configuration["top"]
                + "_cosim.rpt"
            )
            with open(cosim_path, "r") as f:
                # search through cosim report to find out pass/fail status for each language
                for line in f:
                    # if configuration["language"] in line.lower():
                    if "pass" in line.lower():
                        project_status.append("cosim_pass")
                    elif "fail" in line.lower():
                        project_status.append("cosim_fail")
                project_status.append("cosim_done")
            f.close()
        except (OSError, IOError):
            pass
        except:
            pass

        # Pull details from implementation directory, first the presence of an export...
        if os.path.isdir(solution_dict["path"] + "/impl/ip"):
            project_status.append("export_ip_done")
        if os.path.isdir(solution_dict["path"] + "/impl/sysgen"):
            project_status.append("export_sysgen_done")
        # implementation, verilog and vhdl
        if os.path.isfile(
            solution_dict["path"] + "/impl/verilog/" + configuration["top"] + ".v"
        ):
            project_status.append("implementation_verilog")
        if os.path.isfile(
            solution_dict["path"] + "/impl/vhdl/" + configuration["top"] + ".vhd"
        ):
            project_status.append("implementation_vhdl")
        # export
        if os.path.isfile(
            solution_dict["path"]
            + "/impl/report/verilog/"
            + configuration["top"]
            + "_export.rpt"
        ):
            project_status.append("export_verilog")
        if os.path.isfile(
            solution_dict["path"]
            + "/impl/report/vhdl/"
            + configuration["top"]
            + "_export.rpt"
        ):
            project_status.append("export_vhdl")

        #######################
        # print project status
        #######################
        grayinline("\t\t- C Simulation:              ")
        green("Pass") if "csim_pass" in project_status else red(
            "Fail"
        ) if "csim_fail" in project_status else (
            yellow("Run (Can't get status)")
            if "csim_done" in project_status
            else yellow("Not Run")
        )
        grayinline("\t\t- C Synthesis:               ")
        green("Run") if "syn_done" in project_status else yellow("Not Run")
        grayinline("\t\t- C/RTL Co-simulation:       ")
        green("Pass") if "cosim_pass" in project_status else (
            red("Fail")
            if "cosim_fail" in project_status
            else (
                yellow("Run (Can't get status)")
                if "cosim_done" in project_status
                else yellow("Not Run")
            )
        )
        gray("\t\t- Export:")
        grayinline("\t\t\t- IP Catalog:        ")
        green("Run") if "export_ip_done" in project_status else yellow("Not Run")
        grayinline("\t\t\t- System Generator:  ")
        green("Run") if "export_sysgen_done" in project_status else yellow("Not Run")
        grayinline("\t\t\t- Export Evaluation: ")
        green("Run") if "evaluate_done" in project_status else yellow("Not Run")

        if context.args.synthesis_report:
            if os.path.exists(csyn_path):
                gray("\t\t- Synthesis report: " + csyn_path)
                with open(csyn_path, "r") as f:
                    report = f.readlines()
                    for l in report:
                        grayinline("\t\t\t" + l)
            else:
                red("\t\t- No synthesis report found at: " + csyn_path)

        # # NOTE: replaced by --synthesis-report instead
        # try:
        #     with open(csyn_path,'r') as f:
        #         report = f.readlines()

        #         # print the relevant pieces of the report
        #         gray("\t\t- Report:")
        #         # Timing and Latency
        #         for l in report[14:33]:
        #             grayinline("\t\t\t" + l)
        #         #
        #         for l in report[43:64]:
        #             grayinline("\t\t\t" + l)

        # # DEPRECATED: changing between Vitis versions so printing the report
        # # instead of parsing lines.
        # #
        # #         # Fetch line 23:
        # #         #       |ap_clk  |   5.00|     3.492|        0.62|
        # #         report_content = f.readlines()
        # #         # print(report_content)
        # #         ap_clk_line = report_content[22]
        # #         ap_clk_line_elements = [x.strip() for x in ap_clk_line.split('|')]
        # #         clk_target = ap_clk_line_elements[2].split()[0]
        # #         clk_estimated = ap_clk_line_elements[3].split()[0]
        # #         clk_uncertainty = ap_clk_line_elements[4].split()[0]
        # #         gray("\t\t- Clock:")
        # #         grayinline("\t\t\t- Target (ns):       ")
        # #         print(clk_target)
        # #         grayinline("\t\t\t- Estimated (ns):    ")
        # #         green(clk_estimated) if float(clk_estimated) < float(clk_target) else red(clk_estimated)
        # #         grayinline("\t\t\t- Uncertainty (ns):  ")
        # #         yellow(clk_uncertainty)
        # #
        #     f.close()
        # except (OSError, IOError):
        #     pass

    def print_summary_solutions(self, configuration):
        """Process existing solutions within a configuration data structure and display a summary of them

        NOTE: this method operates on the configuration data structure that corresponds to one project. If
        multiple projects are available in under the same ROS 2 package, multiple calls to this method
        should be executed.

        NOTE 2: invoke with "--summary" flag. Will ignore status report (which is the default output)

        :param: configuration: data structure with the HLS configuration (see process_tcl for details)
        :rtype None
        """

        # Create data structures to hold the results.
        #  each element in the dictionary contains:
        #     "solutionN": [clk_estimated, float(clk_estimated)*float(interval_max),
        #                        ,bram_utilization, dsp_utilization, ff_utilization, lut_utilization]
        results = {}

        # Solutions, each:
        # {'solution_4ns': {
        #                 'clock': '4',
        #                 'path': '<path-to-ros2-ws>/build-zcu102/simple_adder/project_simpleadder1/solution_4ns'}
        # },
        solutions = configuration["solutions"]

        for s in solutions:
            solution_key = list(s.keys())[0]
            csyn_path = (
                s[solution_key]["path"]
                + "/syn/report/"
                + configuration["top"]
                + "_csynth.rpt"
            )
            # print(csyn_path)
            try:
                with open(csyn_path, "r") as f:
                    results_from_solution = []

                    # Fetch line 23:
                    #       |ap_clk  |   5.00|     3.492|        0.62|
                    report_content = f.readlines()
                    ap_clk_line = report_content[22]
                    ap_clk_line_elements = [x.strip() for x in ap_clk_line.split("|")]
                    clk_target = ap_clk_line_elements[2].split()[0]
                    clk_estimated = ap_clk_line_elements[3].split()[0]
                    clk_uncertainty = ap_clk_line_elements[4].split()[0]
                    results_from_solution.append(clk_target)
                    results_from_solution.append(clk_estimated)

                    # Fetch line 32, latency in cycles
                    #       |        4|        4|  16.000 ns|  16.000 ns|    5|    5|     none|
                    summary_line = report_content[31]
                    summary_line_elements = [x.strip() for x in summary_line.split("|")]
                    latency_max = summary_line_elements[4].split()[0]
                    # results_from_solution.append((float(clk_estimated) + float(clk_uncertainty))*float(interval_max))
                    results_from_solution.append(latency_max)

                    # Fetch lines 59 and 63
                    #      |Total            |        0|     0|     596|     217|    0|
                    #      |Utilization (%)  |        0|     0|      ~0|      ~0|    0|
                    # By default it's line 63
                    total_line = report_content[58]
                    utilization_line = report_content[62]

                    # these lines may not always be in the same positon thereby we need to search for it
                    # and rewrite it
                    for i in range(len(report_content)):
                        if "Utilization" in report_content[i]:
                            utilization_line = report_content[i]
                            total_line = report_content[i - 4]

                    # parse utilization %
                    utilization_line_elements = [
                        x.strip() for x in utilization_line.split("|")
                    ]
                    bram_utilization = utilization_line_elements[2]
                    dsp_utilization = utilization_line_elements[3]
                    ff_utilization = utilization_line_elements[4]
                    lut_utilization = utilization_line_elements[5]

                    # parse total
                    total_line_elements = [x.strip() for x in total_line.split("|")]
                    bram_total = total_line_elements[2]
                    dsp_total = total_line_elements[3]
                    ff_total = total_line_elements[4]
                    lut_total = total_line_elements[5]

                    results_from_solution.append(bram_total)
                    results_from_solution.append(bram_utilization)
                    results_from_solution.append(dsp_total)
                    results_from_solution.append(dsp_utilization)
                    results_from_solution.append(ff_total)
                    results_from_solution.append(ff_utilization)
                    results_from_solution.append(lut_total)
                    results_from_solution.append(lut_utilization)

                    # append results from this iteration in the general dictionary
                    results[solution_key] = results_from_solution

                f.close()
            except IOError:
                pass
            except IndexError:
                continue

        # Create data structures to hold the results.
        #  each element in the dictionary contains:
        #     "solutionN": [clk_target, clk_estimated, latency_max,
        #                        ,bram_total, bram_utilization, dsp_total, dsp_utilization,
        #                         ff_total, ff_utilization, lut_total, lut_utilization]
        print(
            "Solution#"
            + "\t"
            + "tar.clk"
            + "\t"
            + "est.clk"
            + "\t\t"
            + "latency_max"
            + "\t"
            + "BRAM_18K"
            + "\t"
            + "DSP"
            + "\t"
            + "FF"
            + "\t\t"
            + "LUT"
        )

        # Order dict according to time, (element[2])
        try:
            results = sorted(results.items(), key=lambda x: float(x[1][2]))
        except ValueError:
            pass  # wasn't able to order them

        # Print results
        if type(results) is list:
            for key, element in results:
                print(
                    str(key)
                    + "\t"
                    + str(element[0])
                    + "\t"
                    + str(element[1])
                    + "\t\t"
                    + str(element[2])
                    + "\t\t"
                    + str(element[3])
                    + " ("
                    + str(element[4])
                    + "%)\t\t"
                    + str(element[5])
                    + " ("
                    + str(element[6])
                    + "%)\t"
                    + str(element[7])
                    + " ("
                    + str(element[8])
                    + "%)\t"
                    + str(element[9])
                    + " ("
                    + str(element[10])
                    + "%)\t"
                )
        else:
            for key, element in results.items():
                print(
                    str(key)
                    + "\t"
                    + str(element[0])
                    + "\t"
                    + str(element[1])
                    + "\t\t"
                    + str(element[2])
                    + "\t\t"
                    + str(element[3])
                    + " ("
                    + str(element[4])
                    + "%)\t\t"
                    + str(element[5])
                    + " ("
                    + str(element[6])
                    + "%)\t"
                    + str(element[7])
                    + " ("
                    + str(element[8])
                    + "%)\t"
                    + str(element[9])
                    + " ("
                    + str(element[10])
                    + "%)\t"
                )

    def main(self, *, context):  # noqa: D102
        if not context.args.package_name:
            red("Provide package_name argument")
            sys.exit(1)

        package_paths_tcl = self.find_tcl_package(context.args.package_name)
        if len(package_paths_tcl) > 0:
            pass
        else:
            yellow("No HLS Tcl scripts found for package: " + context.args.package_name)

        ########
        # run
        ########
        if context.args.run:  # run Tcl scripts
            for tcl in package_paths_tcl:
                if not context.args.silent:
                    print(
                        'Found Tcl script "'
                        + tcl.split("/")[-1]
                        + '" for package: '
                        + context.args.package_name
                    )
                    print("Executing " + tcl)

                # launch
                self.run_tcl(context, tcl)
            # sys.exit(0)

        ########
        # summary
        ########
        if context.args.summary:
            for tcl in package_paths_tcl:
                gray(
                    "# " + str(tcl)
                )  # print which project, differentiate when multiple available
                configuration = self.process_tcl(tcl)
                solutions = configuration["solutions"]
                if len(solutions) > 0:
                    self.print_summary_solutions(configuration)
            sys.exit(0)

        ########
        # status
        ########
        if not context.args.silent:
            for tcl in package_paths_tcl:
                configuration = self.process_tcl(tcl)
                solutions = configuration["solutions"]
                if len(solutions) > 0:
                    grayinline("Project: ")
                    print(configuration["project"])
                    grayinline("Path: ")
                    print(configuration["path"])
                    for s in solutions:
                        self.print_status_solution(s, configuration, context)
