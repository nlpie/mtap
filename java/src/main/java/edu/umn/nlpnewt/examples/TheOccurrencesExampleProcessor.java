/*
 * Copyright 2019 Regents of the University of Minnesota
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package edu.umn.nlpnewt.examples;

import edu.umn.nlpnewt.*;
import org.jetbrains.annotations.NotNull;

import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Processor("nlpnewt-example-processor-java")
public class TheOccurrencesExampleProcessor extends AbstractDocumentProcessor {
  private final Pattern pattern = Pattern.compile("\\w+");

  @Override
  protected void process(@NotNull Document document, @NotNull JsonObject params, JsonObject.@NotNull Builder result) {
    if (!params.getBooleanValue("do_work")) {
      return;
    }
    Timer timer = Newt.timingInfo().start("fetch_time");
    String text = document.getText();
    timer.stop();

    try (Labeler<GenericLabel> thesLabeler = document.getLabeler("nlpnewt.examples.thes", true)) {
      Matcher matcher = pattern.matcher(text);
      while (matcher.find()) {
        if ("the".equals(matcher.group())) {
          thesLabeler.add(GenericLabel.builder(matcher.start(), matcher.end()).build());
        }
      }
    }

    result.setProperty("answer", 42);
  }
}
