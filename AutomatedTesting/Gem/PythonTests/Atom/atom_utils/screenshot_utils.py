"""
Copyright (c) Contributors to the Open 3D Engine Project.
For complete copyright and license terms please see the LICENSE at the root of this distribution.

SPDX-License-Identifier: Apache-2.0 OR MIT
"""
import azlmbr.atom
import azlmbr.utils
import azlmbr.legacy.general as general

from editor_python_test_tools.editor_test_helper import EditorTestHelper

DEFAULT_FRAME_WIDTH = 1920
DEFAULT_FRAME_HEIGHT = 1080
FOLDER_PATH = '@user@/PythonTests/Automated/Screenshots'

helper = EditorTestHelper(log_prefix="Atom_ScreenshotHelper")


class ScreenshotHelper(object):
    """
    A helper to capture screenshots and wait for them.
    """

    def __init__(self, idle_wait_frames_callback, frame_width=DEFAULT_FRAME_WIDTH, frame_height=DEFAULT_FRAME_HEIGHT):
        super().__init__()
        self.done = False
        self.capturedScreenshot = False
        self.max_frames_to_wait = 60
        self.prepare_viewport_for_screenshot(frame_width, frame_height)
        self.idle_wait_frames_callback = idle_wait_frames_callback

    def capture_screenshot_blocking_in_game_mode(self, filename):
        helper.enter_game_mode(["", ""])
        general.idle_wait_frames(120)
        self.capture_screenshot_blocking(filename)
        helper.exit_game_mode(["", ""])

    def prepare_viewport_for_screenshot(self, frame_width, frame_height):
        cur_viewport_size = general.get_viewport_size()
        if int(cur_viewport_size.x) != frame_width or int(cur_viewport_size.y) != frame_height:
            general.set_viewport_expansion_policy('FixedSize')
            general.idle_wait_frames(1)
            general.set_viewport_size(frame_width, frame_height)
            general.set_cvar_integer('r_DisplayInfo', 0)
            general.update_viewport()
            general.idle_wait_frames(120)

        new_viewport_size = general.get_viewport_size()
        if int(new_viewport_size.x) != frame_width or int(new_viewport_size.y) != frame_height:
            general.log("Resolution is incorrect!")
            general.log(f"width: {int(new_viewport_size.x)}")
            general.log(f"height: {int(new_viewport_size.y)}")

    def capture_screenshot_blocking(self, filename, folder_path=FOLDER_PATH):
        """
        Capture a screenshot and block the execution until the screenshot has been written to the disk.
        """
        self.done = False
        self.capturedScreenshot = False
        frameCaptureId = azlmbr.atom.FrameCaptureRequestBus(
            azlmbr.bus.Broadcast, "CaptureScreenshot", f"{folder_path}/{filename}")
        if frameCaptureId != -1:
            self.handler = azlmbr.atom.FrameCaptureNotificationBusHandler()
            self.handler.connect(frameCaptureId)
            self.handler.add_callback('OnFrameCaptureFinished', self.on_screenshot_captured)
            self.wait_until_screenshot()
            general.log("Screenshot taken.")
        else:
            general.log("Screenshot failed")
        return self.capturedScreenshot

    def on_screenshot_captured(self, parameters):
        # the parameters come in as a tuple
        if parameters[0] == azlmbr.atom.FrameCaptureResult_Success:
            general.log(f"screenshot saved: {parameters[1]}")
            self.capturedScreenshot = True
        else:
            general.log(f"screenshot failed: {parameters[1]}")
        self.done = True
        self.handler.disconnect()

    def wait_until_screenshot(self):
        frames_waited = 0
        while self.done == False:
            self.idle_wait_frames_callback(1)
            if frames_waited > self.max_frames_to_wait:
                general.log("timeout while waiting for the screenshot to be written")
                self.handler.disconnect()
                break
            else:
                frames_waited = frames_waited + 1
        general.log(f"(waited {frames_waited} frames)")

def take_screenshot_game_mode(screenshot_name, entity_name=None):
    """
    Enters game mode & takes a screenshot, then exits game mode after.
    :param screenshot_name: name to give the captured screenshot .png file.
    :param entity_name: name of the entity being tested (for generating unique log lines).
    :return: None
    """
    general.enter_game_mode()
    helper.wait_for_condition(lambda: general.is_in_game_mode(), 2.0)
    general.log(f"{entity_name}_test: Entered game mode: {general.is_in_game_mode()}")
    ScreenshotHelper(general.idle_wait_frames).capture_screenshot_blocking(f"{screenshot_name}.png")
    general.idle_wait(1.0)
    general.exit_game_mode()
    helper.wait_for_condition(lambda: not general.is_in_game_mode(), 2.0)
    general.log(f"{entity_name}_test: Exit game mode: {not general.is_in_game_mode()}")

def compare_screenshots(imageA, imageB, min_diff_filter=0.01):
    """
    Compare 2 images through an Ebus call. Image order doesn't matter.
    RMS (root mean square) is used for the difference indicator.
    2 final scores are provided: diff_score, filtered_diff_score (after applying min_diff_filter).
    The higher value the more different.
    :param imageA: one of the image.
    :param imageB: the other image.
    :param min_diff_filter: diff values less than this will be filtered out when calculating filtered_diff_score.
    :return: a class ImageDiffResult, containing result_code (Success, FormatMismatch, SizeMismatch, UnsupportedFormat),
        diff_score, filtered_diff_score.
    """
    imageDiffResult = azlmbr.atom.FrameCaptureTestRequestBus(
        azlmbr.bus.Broadcast, "CompareScreenshots", imageA, imageB, min_diff_filter)

    return imageDiffResult

def screenshot_compare_result_code_to_string(result_code):
    """
    Convert the ImageDiffResult.result_code from value to string for debugging purpose.
    :param result_code: the value form of the result code.
    :return: the string form of the result code.
    """
    value_to_string = {
        azlmbr.utils.ImageDiffResultCode_FormatMismatch : "FormatMismatch",
        azlmbr.utils.ImageDiffResultCode_UnsupportedFormat : "UnsupportedFormat",
        azlmbr.utils.ImageDiffResultCode_Success : "Success",
        azlmbr.utils.ImageDiffResultCode_SizeMismatch : "SizeMismatch"}

    return value_to_string[result_code];
