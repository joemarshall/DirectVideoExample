import argparse
import subprocess
from pathlib import Path
import json

BUILD_PLUGINS = {"PICOXR":"pico","ViveOpenXR":"vivefocus","OculusXR":"quest","":"android"}



parser = argparse.ArgumentParser(
                    prog='MakeReleases',
                    description='Makes releases of directvideoexample for a particular target device',
                    )
                    
parser.add_argument("device",nargs="+",help="One or more devices to build for, or 'all' to build everything. Supported devices ("+",".join([f"{x[1]}" for x in BUILD_PLUGINS.items()])+",all)")

args = parser.parse_args()


enabled_build_plugins={}
if "all" in args.device:
    enabled_build_plugins=BUILD_PLUGINS
else:
    for enable_plugin,out_folder in BUILD_PLUGINS.items():
        if out_folder in args.device:
            enabled_build_plugins[enable_plugin]=out_folder
    
    

print("Building for:",list(enabled_build_plugins.values()))
print("*****************************")
project_file = list(Path(__file__).parent.glob("*.uproject"))[0]

orig_text = project_file.read_text()
data = json.loads(orig_text)

release_folder = Path(__file__).parent / "Releases"
release_folder.mkdir(exist_ok=True)


for enable_plugin,out_folder in enabled_build_plugins.items():
    for plugin_info in data["Plugins"]:
        name = plugin_info["Name"]
        if name == enable_plugin:
            plugin_info["Enabled"]=True
        elif name in BUILD_PLUGINS:
            plugin_info["Enabled"]=False
            
    project_file.write_text(json.dumps(data))
    print(f"Building for {enable_plugin}in Releases/{out_folder}")
    platform_folder = release_folder / out_folder
    platform_folder.mkdir(exist_ok=True)
    subprocess.check_call(["d:\\epic\\UE_5.3\\Engine\\Build\\BatchFiles\\RunUAT.bat","buildcookrun",f"-project={str(project_file)}","-platform=android",
                    "-build","-stage","-package","-pak","-cook","-compressed","-configuration=Shipping","-archive", f"-archivedirectory={platform_folder}"  ],shell=True)
    
project_file.write_text(orig_text)    

import sys
sys.exit(1)


    


#"call d:\epic\UE_5.3\Engine\Build\BatchFiles\RunUAT.bat buildcookrun -project=d:\wizdish\videotest\DirectVideoExample\DirectVideoExample.uproject  -platform=android -build -stage -package -pak -cook -compressed -configuration=Release"
