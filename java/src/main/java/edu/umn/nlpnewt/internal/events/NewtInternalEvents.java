/*
 * Copyright 2019 Regents of the University of Minnesota.
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

package edu.umn.nlpnewt.internal.events;

import edu.umn.nlpnewt.Config;
import edu.umn.nlpnewt.Label;
import edu.umn.nlpnewt.LabelIndex;
import edu.umn.nlpnewt.NewtEvents;
import org.jetbrains.annotations.NotNull;

import javax.annotation.Nullable;
import java.util.List;

public final class NewtInternalEvents {
  private NewtInternalEvents() {
    throw new UnsupportedOperationException();
  }

  public static NewtEvents createEvents(Config config, @Nullable String address) {
    EventsClientImpl eventsClient = EventsClientImpl.create(config, address);
    return new NewtEventsImpl(eventsClient);
  }

  public static <L extends Label> @NotNull LabelIndex<@NotNull L> standardLabelIndex(
      @NotNull List<@NotNull L> labels
  ) {
    return StandardLabelIndex.create(labels);
  }

  public static <L extends Label> @NotNull LabelIndex<@NotNull L> distinctLabelIndex(
      @NotNull List<@NotNull L> labels
  ) {
    return DistinctLabelIndex.create(labels);
  }
}
