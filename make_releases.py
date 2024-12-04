import argparse
import subprocess
from pathlib import Path
import json
import shutil
import re
from typing import Callable
import sys
from datetime import datetime

from dataclasses import dataclass

class UnrealIni:
    def __init__(self,content:str):
        subsectionmatch = re.compile(r"\[(.*)\]")
        valuematch = re.compile(r"([^=]*)=(.*)")
        subsections=[]
        cur_section=[]
        cur_section_name=[]
        for line in content.splitlines():
            m1 = subsectionmatch.match(line)
            m2 = valuematch.match(line)
            if m1 is not None:
                if len(cur_section)>0:
                    subsections.append((cur_section_name,cur_section))
                cur_section_name = m1.group(1)
                cur_section=[]
            elif m2 is not None:
                cur_section.append((m2.group(1),m2.group(2)))
        if len(cur_section)>0:
            subsections.append((cur_section_name,cur_section))
        self.subsections=subsections
        assert (self.reconstruct().strip("\n")==content.strip("\n"))
        
    def reconstruct(self):
        reconstructed = ""
        for name,values in self.subsections:
            reconstructed+="["+name+"]\n"
            for k,v in values:
                reconstructed+=f"{k}={v}\n"
            reconstructed+="\n"
        return reconstructed
        
    def update_value(self,enabled,value,modifier):
        done_update=False
        (target_section,target_key) = value
        for name,values in self.subsections:
            if name==target_section:
                for i,(k,v) in enumerate(values):
                    if k==target_key:
                        done_update=True
                        values[i]=[k,modifier(enabled,v)]
        print(self.reconstruct())
                
@dataclass
class BuildFlavour:
    flavour_name: str
    plugin_name : str
    engine_keys: dict|None = None
    
    def update_uproject(self,project_dict:dict,enabled:bool):
        for plugin_info in project_dict["Plugins"]:
            name = plugin_info["Name"]
            if name == self.plugin_name:
                plugin_info["Enabled"]=enabled

    def update_defaultengine(self,config_ini:UnrealIni,enabled:bool):    
        if self.engine_keys!=None:
            for val,modifier in self.engine_keys:
                config_ini.update_value(enabled,val,modifier)
        return config_ini.reconstruct()
    
    

BUILD_FLAVOURS = [
    BuildFlavour("pico","PICOXR"),
    BuildFlavour("vivefocus","ViveOpenXR"),
    BuildFlavour("quest","OculusXR",[
        (("/Script/AndroidRuntimeSettings.AndroidRuntimeSettings","bPackageForMetaQuest"),lambda enabled,current:str(enabled)),
        (("/Script/AndroidRuntimeSettings.AndroidRuntimeSettings","ExtraApplicationSettings"),lambda enabled,current:r'<meta-data android:name="com.oculus.supportedDevices" android:value="quest|quest2|questpro" />' if enabled else ""),
        ]),
BuildFlavour("android","")
]




parser = argparse.ArgumentParser(
                    prog='MakeReleases',
                    description='Makes releases of directvideoexample for a particular target device',
                    )

subparsers = parser.add_subparsers(help='Command to run',required=True,dest="command")
parser_launch = subparsers.add_parser('launch', help='Launch the uproject in Unreal Editor')
parser_launch.add_argument('engine_version', help='Version of editor to run')
parser_launch.add_argument("--ue-path","-ue",default="d:\\epic\\",help="Path to folder containng Unreal Engine versions",type=Path)
parser_build = subparsers.add_parser('build', help='Build the example')
parser_build.add_argument("--ue-path","-ue",default="d:\\epic\\UE_5.3\\",help="Path to Unreal Engine")
parser_build.add_argument("device",nargs="+",help="One or more devices to build for, or 'all' to build everything.",choices = [x.flavour_name for x in BUILD_FLAVOURS]+["all"])
parser_build.add_argument("--development","-d",help="make development build",action="store_true")
parser_build.add_argument("--install","-i",help="install to device after build",action="store_true")
parser_build.add_argument("--run","-r",help="Run app after build",action="store_true")
parser_build.add_argument("--grablog","-g",help="Run app and save log to log_<date>.txt",action="store_true")
parser_build.add_argument("--logname","-l",help="Set log text file name")
parser_build.add_argument("--sanitizer","-s",help="Set sanitizer",choices=["asan","ubsan","tsan"])
validation_group = parser_build.add_mutually_exclusive_group()
validation_group.add_argument("--validation",help="Do vulkan validation",action="store_true")
validation_group.add_argument("--novalidation",help="Don't do vulkan validation",action="store_false")
parser_release = subparsers.add_parser('release', help='Upload github release')

parser_release.add_argument("version",help="version tag for release")
parser_release.add_argument("--force","-f",help="Update existing release if tag exists",action="store_true")
args = parser.parse_args()

project_folder = Path(__file__).parent

project_short_name = project_folder.name


project_file = list(project_folder.glob("*.uproject"))[0]
defaultengine_file = (project_folder / "Config/DefaultEngine.ini")
if args.command=="build" and args.development:
    release_folder = Path(__file__).parent / "DevReleases"
else:
    release_folder = Path(__file__).parent / "Releases"

def command_launch(args):
    ue_base_path = args.ue_path
    if re.match(r"UE_\d+\.\d+",ue_base_path.name):
        # path to a single engine, get parent path to choose version
        ue_base_path = ue_base_path.parent
    version=args.engine_version
    version_groups = re.match(r"(\d+)\.(\d+)(.(\d+))*",version)
    editor_path = None
    if version_groups:
        maj= version_groups.group(1)
        min=version_groups.group(2)
        editor_path = ue_base_path / f"UE_{maj}.{min}" / "Engine" / "Binaries" / "Win64" / "UnrealEditor.exe"
    if editor_path and editor_path.exists():
        subprocess.Popen([editor_path,project_file])
    else:
        print(f"Bad engine version number {args.engine_version}:{editor_path}")
        sys.exit(-1)
    
def command_build(args):
    use_validation_layer=False
    if args.development:
        use_validation_layer=args.novalidation
    else:
        use_validation_layer=args.validation
        

    enabled_build_plugins=[]
    if "all" in args.device:
        enabled_build_plugins=BUILD_FLAVOURS
    else:
        for f in BUILD_FLAVOURS:
            if f.flavour_name in args.device:
                enabled_build_plugins.append(f)
    
    if args.install:
        if len(enabled_build_plugins)!=1:
            print("Can only call install with a single build flavour")
            sys.exit(-1)
        
    print("Building for:",[f.flavour_name for f in enabled_build_plugins])
    print("*****************************")

    orig_project_file = project_file.read_text()
    uproject_data = json.loads(orig_project_file)
    orig_defaultengine_file = defaultengine_file.read_text()

    try:
        defaultengine_data = UnrealIni(orig_defaultengine_file)

        release_folder.mkdir(exist_ok=True)

        for current_flavour in enabled_build_plugins:
            for all_flavour in BUILD_FLAVOURS:
                enabled = all_flavour.flavour_name == current_flavour.flavour_name
                all_flavour.update_uproject(uproject_data,enabled)
                all_flavour.update_defaultengine(defaultengine_data,enabled)

            # do vulkan validation in dev builds (or if --validation is on)
            for plugin_info in uproject_data["Plugins"]:
                name = plugin_info["Name"]
                if name=="AndroidVulkanValidation":
                    plugin_info["Enabled"]=use_validation_layer

            project_file.write_text(json.dumps(uproject_data,indent=4))
            defaultengine_file.write_text(defaultengine_data.reconstruct())

            platform_folder = release_folder / current_flavour.flavour_name
            print(f"Building for {current_flavour.flavour_name} in {platform_folder}")
            if platform_folder.exists():
                shutil.rmtree(platform_folder,ignore_errors=True)
            platform_folder.mkdir(exist_ok=True)
            if args.development:
                config="Development"
            else:
                config="Shipping"
                
            cmdline = [f"{args.ue_path}\\Engine\\Build\\BatchFiles\\RunUAT.bat","buildcookrun",f"-project={str(project_file)}","-platform=android",
                            "-build","-stage","-package","-pak","-cook","-compressed",f"-configuration={config}","-archive", f"-archivedirectory={platform_folder}"  ]
            if args.sanitizer:
                cmdline.append({"asan":"-EnableASan","ubsan":"-EnableUBSan","tsan":"-EnableTSan"}[args.sanitizer])
            subprocess.check_call(cmdline,shell=True)
            # if the build is to a subfolder of the target folder (e.g. Android / Android_ASTC etc.) then move that up one
            if (platform_folder / "Android").exists():
                for x in (platform_folder / "Android").iterdir():
                    shutil.move(x,platform_folder)
                    
            if args.install or args.run or args.grablog:
                # find the install batch file
                for b in platform_folder.glob("*.bat"):
                    if b.name.lower().startswith("install"):
                        subprocess.check_call([str(b)],shell=True,cwd=str(platform_folder))
                        break

            if args.grablog:
                subprocess.check_call(["adb","logcat","-c"],shell=True,cwd=str(project_folder))
            
            if args.run or args.grablog:
               subprocess.check_call(["adb","shell","am","start","-n","com.YourCompany.DirectVideoExample/com.epicgames.unreal.GameActivity"])
               
            if args.grablog:
                if args.logname:
                    log_name=args.logname
                else:
                    now=datetime.now()
                    log_name=now.strftime(f"{project_short_name}-%Y_%m_%d-%H_%M_%S.txt")
                print(f"Grabbing log to {log_name}. Press ctrl+c to exit")
                subprocess.check_call(["adb","logcat",">",str(log_name)],shell=True,cwd=str(project_folder))
                
    finally:
        project_file.write_text(orig_project_file)    
        defaultengine_file.write_text(orig_defaultengine_file)

def command_release(args):
    version = args.version
    if not version.startswith("v"):
        version="v"+version
    print("Version:",version)
    cmdline = ["gh","release","create",version,"--notes",f"Release {version}"]
    if args.force:
        # ignore if release already exists
        subprocess.call(cmdline)
    else:
        subprocess.check_call(cmdline)
    uploading_zips=[]
    for subfolder in release_folder.iterdir():
        if subfolder.is_dir():
            # make a zip from this folder
            print(f"Making zip {subfolder}")
            uploading_zips.append(shutil.make_archive(str(subfolder),format='zip',root_dir=subfolder,base_dir=subfolder))
    print("Uploading:",*uploading_zips)
    subprocess.check_call(["gh","release","upload",version,"--clobber"]+[str(x) for x in uploading_zips])
    

    
locals()["command_"+args.command](args)
