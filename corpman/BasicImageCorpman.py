# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
BasicImageCorpusManager is a CorpusManager that uses the loki fuzzer to mutate
data and embed it in a document suitable for processing by a web browser.
"""

__author__ = "Tyson Smith"
__credits__ = ["Tyson Smith"]

import base64
import random

import corpman
import loki

class BasicImageCorpusManager(corpman.CorpusManager):
    key = "image_basic"

    def _init_fuzzer(self, aggression):
        self._fuzzer = loki.Loki(aggression)


    @staticmethod
    def _random_dimention():
        choice = random.randint(0, 2)
        if choice == 0:
            return random.randint(1, 0xFF)
        elif choice == 1:
            return (2**random.randint(2, 16)) + random.randint(-2, 2)
        elif choice == 2: # favor small to stress downscaler
            return random.randint(1, 4)


    def generate(self, media_type=None, redirect_page="done", timeout=5000):
        self._rotate_template()

        # prepare data for playback
        if self._is_replay:
            self._test.fuzzed_data = self._test.template_data
        else:
            self._test.fuzzed_data = self._fuzzer.fuzz_data(self._test.template_data)

        if media_type is None:
            if self._test.extension in ("jpeg", "jpg"):
                media_type = "image/jpeg"
            elif self._test.extension == "ico":
                media_type = "image/x-icon"
            elif self._test.extension in ("bmp", "gif", "png"):
                media_type = "image/%s" % self._test.extension
            else:
                media_type = "application/octet-stream"

        fuzzed_img = "data:%s;base64,%s" % (
            media_type,
            base64.standard_b64encode(self._test.fuzzed_data))

        self._test.test_data = "\n".join([
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<meta http-equiv='Cache-control' content='no-cache'>",
            "</head>",
            "<body>",
            "<img id='m1' src='%s'>" % fuzzed_img,
            "<img id='m2' height='2' width='2'>",
            "<canvas id='c1'></canvas>",
            "<script>",
            "  var tmr;",
            "  var im1=document.getElementById('m1');",
            "  function reset(){",
            "    clearTimeout(tmr);",
            "    window.location='/%s';" % redirect_page,
            "  }",
            "  im1.addEventListener('error', reset, true);",
            "  window.onload=function(){",
            "    var im2=document.getElementById('m2');",
            "    im2.src=im1.src;",
            "    var ctx=document.getElementById('c1').getContext('2d');",
            "    ctx.drawImage(im1, 0, 0); // sync docoder call",
            "    ctx.drawImage(im2, 0, 0); // sync downscaler call",
            "    im2.height=%d;" % self._random_dimention(),
            "    im2.width=%d;" % self._random_dimention(),
            "    ctx.drawImage(im2, 0, 0);",
            "    reset();",
            "  }",
            "  tmr=setTimeout(reset, %d); // timeout" % timeout,
            "</script>",
            "</body>",
            "</html>"
        ])

        self._gen_count += 1