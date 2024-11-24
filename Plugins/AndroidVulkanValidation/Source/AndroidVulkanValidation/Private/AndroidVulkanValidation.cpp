// Copyright Epic Games, Inc. All Rights Reserved.

#include "AndroidVulkanValidation.h"

#include "IVulkanDynamicRHI.h"

#define LOCTEXT_NAMESPACE "FAndroidVulkanValidationModule"

DEFINE_LOG_CATEGORY(LogAndroidVulkanValidation);

void FAndroidVulkanValidationModule::StartupModule()
{
    const TArray<const ANSICHAR *> InstanceLayers = {"VK_LAYER_KHRONOS_validation"};
    // enable debug utils extension so that debug code works
    const TArray<const ANSICHAR *> InstanceExtensions = {"VK_EXT_debug_utils"};
    IVulkanDynamicRHI::AddEnabledInstanceExtensionsAndLayers(InstanceExtensions, InstanceLayers);

    const TArray<const ANSICHAR *> DeviceLayers = {};
    const TArray<const ANSICHAR*> DeviceExtensions = {"VK_EXT_debug_marker"};
    IVulkanDynamicRHI::AddEnabledDeviceExtensionsAndLayers(DeviceExtensions, DeviceLayers);

    UE_LOG(LogAndroidVulkanValidation, Verbose, TEXT("Enabled debug extension and validation layer"));

}

void FAndroidVulkanValidationModule::ShutdownModule()
{
    // This function may be called during shutdown to clean up your module.  For modules that
    // support dynamic reloading, we call this function before unloading the module.
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FAndroidVulkanValidationModule, AndroidVulkanValidation)