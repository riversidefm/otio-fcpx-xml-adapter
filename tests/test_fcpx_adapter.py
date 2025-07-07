# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the OpenTimelineIO project

import os
import subprocess
import sys
import unittest
import unittest.mock
import opentimelineio as otio
import opentimelineio.test_utils as otio_test_utils
from otio_fcpx_xml_adapter.fcpx_xml import FFProbe


SAMPLE_LIBRARY_XML = os.path.join(
    os.path.dirname(__file__),
    "sample_data",
    "fcpx_library.fcpxml"
)
SAMPLE_PROJECT_XML = os.path.join(
    os.path.dirname(__file__),
    "sample_data",
    "fcpx_project.fcpxml"
)
SAMPLE_EVENT_XML = os.path.join(
    os.path.dirname(__file__),
    "sample_data",
    "fcpx_event.fcpxml"
)
SAMPLE_CLIPS_XML = os.path.join(
    os.path.dirname(__file__),
    "sample_data",
    "fcpx_clips.fcpxml"
)


class AdaptersFcpXXmlTest(unittest.TestCase, otio_test_utils.OTIOAssertions):
    """
    The test class for the FCP X XML adapter
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

    def test_library_roundtrip(self):
        container = otio.adapters.read_from_file(SAMPLE_LIBRARY_XML)
        timeline = container.find_children(
            descended_from_type=otio.schema.Timeline)[0]

        self.assertIsNotNone(timeline)
        self.assertEqual(len(timeline.tracks), 4)

        self.assertEqual(len(timeline.video_tracks()), 3)
        self.assertEqual(len(timeline.audio_tracks()), 1)

        video_clip_names = (
            (
                'IMG_0715',
                "",
                'compound_clip_1',
                'IMG_0233',
                'IMG_0687',
                'IMG_0268',
                'compound_clip_1'
            ),
            ("", 'IMG_0513', "", 'IMG_0268', 'IMG_0740'),
            ("", 'IMG_0857')
        )

        for n, track in enumerate(timeline.video_tracks()):
            self.assertTupleEqual(
                tuple(c.name for c in track),
                video_clip_names[n]
            )

        fcpx_xml = otio.adapters.write_to_string(container, "fcpx_xml")
        self.assertIsNotNone(fcpx_xml)

        new_timeline = otio.adapters.read_from_string(fcpx_xml, "fcpx_xml")
        self.assertJsonEqual(container, new_timeline)

    def test_event_roundtrip(self):
        container = otio.adapters.read_from_file(SAMPLE_EVENT_XML)
        timeline = container.find_children(
            descended_from_type=otio.schema.Timeline)[0]

        self.assertIsNotNone(timeline)
        self.assertEqual(len(timeline.tracks), 4)

        self.assertEqual(len(timeline.video_tracks()), 3)
        self.assertEqual(len(timeline.audio_tracks()), 1)

        video_clip_names = (
            (
                'IMG_0715',
                "",
                'compound_clip_1',
                'IMG_0233',
                'IMG_0687',
                'IMG_0268',
                'compound_clip_1'
            ),
            ("", 'IMG_0513', "", 'IMG_0268', 'IMG_0740'),
            ("", 'IMG_0857')
        )

        for n, track in enumerate(timeline.video_tracks()):
            self.assertTupleEqual(
                tuple(c.name for c in track),
                video_clip_names[n]
            )

        fcpx_xml = otio.adapters.write_to_string(container, "fcpx_xml")
        self.assertIsNotNone(fcpx_xml)

        new_timeline = otio.adapters.read_from_string(fcpx_xml, "fcpx_xml")
        self.assertJsonEqual(container, new_timeline)

    def test_project_roundtrip(self):
        timeline = otio.adapters.read_from_file(SAMPLE_PROJECT_XML)

        self.assertIsNotNone(timeline)
        self.assertEqual(len(timeline.tracks), 4)

        self.assertEqual(len(timeline.video_tracks()), 3)
        self.assertEqual(len(timeline.audio_tracks()), 1)

        video_clip_names = (
            (
                'IMG_0715',
                "",
                'compound_clip_1',
                'IMG_0233',
                'IMG_0687',
                'IMG_0268',
                'compound_clip_1'
            ),
            ("", 'IMG_0513', "", 'IMG_0268', 'IMG_0740'),
            ("", 'IMG_0857')
        )

        for n, track in enumerate(timeline.video_tracks()):
            self.assertTupleEqual(
                tuple(c.name for c in track),
                video_clip_names[n]
            )

        fcpx_xml = otio.adapters.write_to_string(timeline, "fcpx_xml")
        self.assertIsNotNone(fcpx_xml)

        new_timeline = otio.adapters.read_from_string(fcpx_xml, "fcpx_xml")
        self.assertJsonEqual(timeline, new_timeline)

    def test_clips_roundtrip(self):
        container = otio.adapters.read_from_file(SAMPLE_CLIPS_XML)
        fcpx_xml = otio.adapters.write_to_string(container, "fcpx_xml")
        self.assertIsNotNone(fcpx_xml)

        new_timeline = otio.adapters.read_from_string(fcpx_xml, "fcpx_xml")
        self.assertJsonEqual(container, new_timeline)

    def test_format_name(self):
        rvalue = subprocess.check_output(
            [sys.executable, '-c', 'print("640x360x25/1")']
        )
        mock_patch = unittest.mock.patch.object
        with mock_patch(subprocess, 'check_output', return_value=rvalue):
            with mock_patch(os.path, 'exists', return_value=True):
                ffprobe = FFProbe("file:///dummy.me")
                ffprobe.probe()
                self.assertEqual(
                    ffprobe.format_name(),
                    'FFVideoFormat360p25'
                )

    def test_audio_only_format(self):
        """Test audio-only file handling."""
        # Mock ffprobe responses: first call (video) fails, second call (audio) succeeds
        def mock_check_output(*args, **kwargs):
            command = args[0]
            if "v:0" in command:
                # Video probe - raise exception (no video stream)
                raise subprocess.CalledProcessError(1, command)
            elif "a:0" in command:
                # Audio probe - return sample rate and channels
                return b"48000x2\n"
            else:
                raise subprocess.CalledProcessError(1, command)

        mock_patch = unittest.mock.patch.object
        with mock_patch(subprocess, 'check_output', side_effect=mock_check_output):
            with mock_patch(os.path, 'exists', return_value=True):
                ffprobe = FFProbe("file:///dummy.wav")
                ffprobe.probe()

                # Check audio properties
                self.assertTrue(ffprobe.has_audio())
                self.assertFalse(ffprobe.has_video())
                self.assertTrue(ffprobe.is_audio_only())
                self.assertEqual(ffprobe.audio_sample_rate, 48000)
                self.assertEqual(ffprobe.audio_channels, 2)



if __name__ == '__main__':
    unittest.main()
