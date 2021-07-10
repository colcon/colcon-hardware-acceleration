#    ____  ____
#   /   /\/   /
#  /___/  \  /   Copyright (c) 2021, Xilinx®.
#  \   \   \/    Author: Víctor Mayoral Vilches <victorma@xilinx.com>
#   \   \
#   /   /
#  /___/   /\
#  \   \  /  \
#   \___\/\___\
#

import os
import sys

from colcon_core.package_discovery import discover_packages
from colcon_core.package_identification \
    import get_package_identification_extensions
from colcon_core.plugin_system import satisfies_version
from colcon_krs.subverb import (
    KRSSubverbExtensionPoint,
    check_install_directory,
    get_rawimage_path,
    run,
    get_install_dir,
    get_firmware_dir,
    get_vitis_dir,
    get_vivado_dir,
    exists
)
from colcon_krs.verb import green, yellow, red, greeninline \
    ,redinline, yellowinline, grayinline, magenta, gray


class HLSSubverb(KRSSubverbExtensionPoint):
    """Xilinx Vitis HLS capabilities extension.

    NOTE: Default behavior of this subverb is to show the HLS "status"

    Exposes Vitis HLS suite at the colcon ROS 2 meta build tools level. Provides:
        0. Capability to show the HLS status of a given ROS 2 package
        1. Capability to launch Tcl scripts (pre-generated with ament macros, e.g. see vitis_hls_generate_tcl)
        2. Capability to bring up summarized versions of synthesis reports

    """

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(KRSSubverbExtensionPoint.EXTENSION_POINT_VERSION, "^1.0")

    def add_arguments(self, *, parser):  # noqa: D102

        argument = parser.add_argument(
            "package_name",
            nargs="?",         
            help='Name of the package whereto run HLS',
        )
        argument = parser.add_argument("--verbose", dest="verbose", action="store_true")
        argument = parser.add_argument("--run", dest="run", 
            action="store_true", 
            help='Run HLS from CLI according to the Tcl scripts',)

    def find_tcl_package(self, package_name):
        """Find Tcl scripts for the package_name

        NOTE: silly filtering based on simply substring matching, consider
        more complex filtering with end-of-string if neccessary in the future

        :param string package_name: ROS 2 package name whereto execute HLS
        :rtype list
        """
        current_dir = os.environ.get("PWD", "")
        filter_data = [x for x in os.listdir(current_dir) if
                            all(y in x for y in ["build"])]
        if len(filter_data) < 1:
            red(
            "No build* directories found.\n"
            + "Make sure you're in the root of your ROS 2 workspace and the build "
            + "dir starts with 'build'."
            )
            sys.exit(1)
        
        package_paths = []  # paths under a build* dir that match with package_name
        package_paths_tcl = []  # above, and that contain a .tcl file
        for buildir in filter_data:
            build_current_dir = current_dir + "/" + buildir            
            for x in os.listdir(build_current_dir):
                if all(y in x for y in [package_name]):
                    package_paths.append(build_current_dir + "/" + x) 
    
        for p in package_paths:
            for x in os.listdir(p):
                if all(y in x for y in [".tcl"]):
                    package_paths_tcl.append(p + "/" + x)
        
        # drop any matches of .tcl.in as this is part of the ament generation process
        package_paths_tcl = [x for x in package_paths_tcl if
              all(y not in x for y in [".tcl.in"])]

        return package_paths_tcl

    def process_tcl(self, tcl):
        """Process Tcl script and return a config dict

        NOTE: data structure of the return type is as follows:
            {
                'path': '/home/xilinx/ros2_ws/build-zcu102/simple_adder/project_simpleadder1',
                'project': 'project_simpleadder1',
                'solutions': [
                        {'solution_4ns': {
                                'clock': '4',
                                'path': '/home/xilinx/ros2_ws/build-zcu102/simple_adder/project_simpleadder1/solution_4ns'}
                        },
                        {'solution_10ns': {
                                'clock': '10',
                                'path': '/home/xilinx/ros2_ws/build-zcu102/simple_adder/project_simpleadder1/solution_10ns'}
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
        
        data = open(tcl,'r').read()        
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
            solution = {solutions[i]:{"clock":clocks[i], "path":path + "/" + solutions[i]}}
            tcl_dic["solutions"].append(solution)

        return tcl_dic

    def run_tcl(self, tcl):
        """Run Tcl script with vitis_hls

        :param string tcl: path to Tcl script
        :rtype: None
        """         
        cmd = "cd " + tcl[:tcl.rfind("/")] + " && vitis_hls -f " + tcl
        outs, errs = run(cmd, shell=True)
        if errs:
            red(errs)
            sys.exit(1)
        if context.args.verbose:
            print(outs)

    def print_status_solution(self, solution, configuration):
        """Print the status of a solution

        NOTE: Tested in Vitis 2020.2

        :param solution: solution to print with shape as in
                {'solution_4ns': {'clock': '4', 'path': '/home/xilinx/ros2_ws/build-zcu102/simple_adder/project_simpleadder1/solution_4ns'}}
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
        csimlog_path = solution_dict["path"] + "/csim/report/" + configuration["top"] + "_csim.log"
        try:
            with open(csimlog_path,'r') as f:
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
        csyn_path = solution_dict["path"] + "/syn/report/" + configuration["top"] + "_csynth.rpt"
        if os.path.isfile(csyn_path):
            project_status.append('syn_done')
        
        # Pull details from cosim report
        try:
            cosim_path = solution_dict["path"] + "/sim/report/" + configuration["top"] + "_cosim.rpt"
            with open(cosim_path,'r') as f:
                # search through cosim report to find out pass/fail status for each language
                for line in f:
                    if config["language"] in line.lower():
                        if "pass" in line.lower():
                            project_status.append('cosim_pass')
                        elif "fail" in line.lower():
                            project_status.append('cosim_fail')
                project_status.append('cosim_done')
            f.close()
        except (OSError, IOError):
            pass
        except:
            pass

        # Pull details from implementation directory, first the presence of an export...
        if os.path.isdir(solution_dict["path"] + "/impl/ip"):
            project_status.append('export_ip_done')
        if os.path.isdir(solution_dict["path"] + "/impl/sysgen"):
            project_status.append('export_sysgen_done')
        # implementation, verilog and vhdl        
        if os.path.isfile(solution_dict["path"] + "/impl/verilog/" + configuration["top"] + ".v"):
            project_status.append('implementation_verilog')
        if os.path.isfile(solution_dict["path"] + "/impl/vhdl/" + configuration["top"] + ".vhd"):
            project_status.append('implementation_vhdl')
        # export
        if os.path.isfile(solution_dict["path"] + "/impl/report/verilog/" + configuration["top"] + "_export.rpt"):
            project_status.append('export_verilog')
        if os.path.isfile(solution_dict["path"] + "/impl/report/vhdl/" + configuration["top"] + "_export.rpt"):
            project_status.append('export_vhdl')
        
        #######################
        # print project status
        #######################
        grayinline("\t\t- C Simulation:              ") 
        green("Pass") if "csim_pass" in project_status else red("Fail") if "csim_fail" in project_status \
                else (yellow("Run (Can't get status)") if "csim_done" in project_status else yellow("Not Run"))
        grayinline("\t\t- C Synthesis:               ") 
        green("Run") if "syn_done" in project_status else yellow("Not Run")
        grayinline("\t\t- C/RTL Co-simulation:       ") 
        green("Pass") if "cosim_pass" in project_status else (red("Fail") if "cosim_fail" in project_status \
                else (yellow("Run (Can't get status)") if "cosim_done" in project_status else yellow("Not Run")))                
        gray("\t\t- Export:" )
        grayinline("\t\t\t- IP Catalog:        ") 
        green("Run") if "export_ip_done" in project_status else yellow("Not Run")
        grayinline("\t\t\t- System Generator:  ") 
        green("Run") if "export_sysgen_done" in project_status else yellow("Not Run")
        grayinline("\t\t\t- Export Evaluation: ") 
        green("Run") if "evaluate_done" in project_status else yellow("Not Run")

        try:
            with open(csyn_path,'r') as f:
                report = f.readlines()
                
                # print the relevant pieces of the report
                gray("\t\t- Report:")
                # Timing and Latency
                for l in report[14:33]:
                    grayinline("\t\t\t" + l)
                # 
                for l in report[43:64]:
                    grayinline("\t\t\t" + l)
                
        # DEPRECATED: changing between Vitis versions so printing the report
        # instead of parsing lines.
        #
        #         # Fetch line 23:
        #         #       |ap_clk  |   5.00|     3.492|        0.62|
        #         report_content = f.readlines()
        #         # print(report_content)
        #         ap_clk_line = report_content[22]
        #         ap_clk_line_elements = [x.strip() for x in ap_clk_line.split('|')]
        #         clk_target = ap_clk_line_elements[2].split()[0]
        #         clk_estimated = ap_clk_line_elements[3].split()[0]
        #         clk_uncertainty = ap_clk_line_elements[4].split()[0]
        #         gray("\t\t- Clock:")
        #         grayinline("\t\t\t- Target (ns):       ") 
        #         print(clk_target)
        #         grayinline("\t\t\t- Estimated (ns):    ")
        #         green(clk_estimated) if float(clk_estimated) < float(clk_target) else red(clk_estimated)
        #         grayinline("\t\t\t- Uncertainty (ns):  ")
        #         yellow(clk_uncertainty)
        #
            f.close()
        except (OSError, IOError):
            pass


    def optimize_tcl(self):
        """Enhance Tcl script with additional solutions and \
            optimize time or on resources.

        TODO: see https://github.com/vmayoral/hlsclt/blob/master/hlsclt/optimize_commands/optimize_commands.py
        """
        pass

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
                green("Found Tcl script \"" + tcl.split("/")[-1] + "\" for package: " + context.args.package_name)
                print("Executing " + tcl)

                # launch                
                self.run_tcl(tcl)
            # sys.exit(0)

        ########
        # status
        ########
        for tcl in package_paths_tcl:
            configuration = self.process_tcl(tcl)
            # print(configuration)

            solutions = configuration["solutions"]
            if len(solutions) > 1:
                grayinline("Project: ")
                print(configuration["project"])
                grayinline("Path: ")
                print(configuration["path"])
                for s in solutions:
                    self.print_status_solution(s, configuration)

