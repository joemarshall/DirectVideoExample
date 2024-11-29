# Example Unreal project for DirectVideo plugin

This loads a single 360 video and displays it, both in standard video playback via texture mode, and also in the experimental direct mesh renderer mode (pull a trigger on VR versions, or touch with two fingers on plain Android to switch between render modes).

If you build it without the plugin installed on your engine, it will fall back to standard Android media player, and you will be able to see that Unreal can't play high resolution video at any decent framerate.

To build this project, either load the project in Unreal and you can build it (don't forget to choose a device plugin if you are using a VR headset), or you can use the `make_releases.py` python script to make releases for different devices. Supported devices currently are: Meta Quest 2/3 (**quest**), Pico (**pico**), Vive Focus (**vivefocus**), and stock Android (**android**). You can also download prebuilt versions [in the releases here](https://github.com/joemarshall/DirectVideoExample/releases/latest).

[See more about the plugin here](https://joemarshall.github.io/directvideo/)

[Buy the plugin here](https://www.fab.com/listings/3259a389-1214-4312-a6aa-14fc8012ce7b)


# HowTo: Make a logfile dump

If you are having problems with the plugin, the included `make_releases.py` script can be used to build, run and capture the logs. Call it like this:

```
python make_releases.py build --development --grablog android  
```
(replace android with the device you are using, e.g. quest, pico - call `python make_releases.py build -h` for a list of supported VR devices, and other possible options).