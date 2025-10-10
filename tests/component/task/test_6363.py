import nidaqmx
from nidaqmx.constants import AcquisitionType

def test_device_property_support(device_name, channel_name):
    """
    Test if the device supports the DAQmx_FirstSampClk_When property.

    Args:
        device_name (str): The name of the device (e.g., "PXIe-6363").
        channel_name (str): The name of the channel (e.g., "ai0").
    """
    task = nidaqmx.Task()
    try:
        # Add an analog input channel
        task.ai_channels.add_ai_voltage_chan(f"{device_name}/{channel_name}")
        
        # Set up timing to test property compatibility
        task.timing.cfg_samp_clk_timing(
            rate=1000,
            sample_mode=AcquisitionType.CONTINUOUS,
        )
        task.start()

        # Check if ai_conv_rate is supported
        try:
            timestamp = task.timing.first_samp_clk_when


            assert timestamp >= 0  # Verify timestamp is non-negative
            print(f"first_samp_timestamp_val is supported by the device {device_name}!")
        except nidaqmx.errors.DaqError as e:
            if "Specified property is not supported by the device" in str(e):
                print(f"first_samp_timestamp_val is not supported by the device {device_name}.")
            else:
                raise  # Re-raise unexpected errors

    except nidaqmx.errors.DaqError as e:
        print(f"Unexpected error: {e}")

    finally:
        task.close()

# Example usage
if __name__ == "__main__":
    # Replace with your device and channel name
    test_device_property_support("PXI1Slot2ThisRealPXIE6363", "ai0")