package edu.umn.nlpie.mtap.examples;

import edu.umn.nlpie.mtap.common.JsonObject;
import edu.umn.nlpie.mtap.common.JsonObjectBuilder;
import edu.umn.nlpie.mtap.common.Server;
import edu.umn.nlpie.mtap.model.Document;
import edu.umn.nlpie.mtap.model.GenericLabel;
import edu.umn.nlpie.mtap.model.LabelIndex;
import edu.umn.nlpie.mtap.model.Labeler;
import edu.umn.nlpie.mtap.processing.*;
import org.jetbrains.annotations.NotNull;
import org.kohsuke.args4j.CmdLineException;
import org.kohsuke.args4j.CmdLineParser;

import java.io.IOException;
import java.util.*;

/**
 * Examples showing labels referencing other labels.
 */
@Processor(
    value = "mtap-java-reference-labels-example-processor",
    humanName = "MTAP Java Reference Labels Example",
    description = "Examples of using reference labels in Java",
    outputs = {
        @LabelIndexDescription(
            name = "referenced",
            description = "Labels which are referenced by other labels."
        ),
        @LabelIndexDescription(
            name = "map_references",
            description = "Labels containing a map from strings to labels",
            properties = {
                @PropertyDescription(
                    name = "ref",
                    description = "The map of strings to references",
                    dataType = "dict[str, GenericLabel]"
                )
            }
        ),
        @LabelIndexDescription(
            name = "list_references",
            description = "Labels containing a list of labels.",
            properties = {
                @PropertyDescription(
                    name = "ref",
                    description = "The list of labels.",
                    dataType = "list[GenericLabel]"
                )
            }
        ),
        @LabelIndexDescription(
            name = "references",
            description = "Labels with direct references to other labels.",
            properties = {
                @PropertyDescription(
                    name = "a",
                    description = "The first reference to another label.",
                    dataType = "GenericLabel"
                ),
                @PropertyDescription(
                    name = "b",
                    description = "The second reference to another label.",
                    dataType = "GenericLabel"
                )
            }
        )
    }
)
public class ReferenceLabelsExampleProcessor extends DocumentProcessor {
  @Override
  protected void process(
      @NotNull Document document,
      @NotNull JsonObject params,
      @NotNull JsonObjectBuilder<?, ?> result) {
    List<GenericLabel> referenced = Arrays.asList(
        GenericLabel.createSpan(0, 1),
        GenericLabel.createSpan(1, 2),
        GenericLabel.createSpan(2, 3),
        GenericLabel.createSpan(3, 4)
    );

    // references can be a map of strings to labels
    Map<String, GenericLabel> map = new HashMap<>();
    map.put("a", referenced.get(0));
    map.put("b", referenced.get(1));
    map.put("c", referenced.get(2));
    map.put("d", referenced.get(3));
    List<GenericLabel> mapReference = Collections.singletonList(
        GenericLabel.withSpan(0, 4)
            .setReference("ref", map)
            .build()
    );
    // the referenced labels don't actually need to be uploaded yet.
    document.addLabels("map_references", mapReference);

    // references can be lists of labels
    // using a labeler is equivalent to collecting a set of labels in a list and then uploading
    // them via "addLabels".
    try (Labeler<GenericLabel> labeler = document.getLabeler("list_references")) {
      labeler.add(GenericLabel.withSpan(0, 2)
          .setReference("ref", Arrays.asList(referenced.get(0), referenced.get(1)))
          .build());
      labeler.add(GenericLabel.withSpan(2, 4)
          .setReference("ref", Arrays.asList(referenced.get(2), referenced.get(3)))
          .build());
    }

    // references can be direct
    try (Labeler<GenericLabel> labeler = document.getLabeler("references")) {
      labeler.add(GenericLabel.withSpan(0, 2)
          .setReference("a", referenced.get(0))
          .setReference("b", referenced.get(1)));
      labeler.add(GenericLabel.withSpan(2, 4)
          .setReference("a", referenced.get(2))
          .setReference("b", referenced.get(3))
          .build());
    }
    // accessing label references
    LabelIndex<GenericLabel> labelIndex = document.getLabelIndex("references");
    List<@NotNull GenericLabel> labels = labelIndex.asList();
    assert labels.get(0).getReferentialValue("a") == referenced.get(0);

    // referenced labels don't need to be added via "addLabels" or "Labeler.close" before label
    // indices that reference them.
    // The Document will delay uploading any label indices to the server until they are.
    document.addLabels("referenced", referenced);
  }

  public static void main(String[] args) {
    ProcessorServer.Builder options = new ProcessorServer.Builder();
    CmdLineParser parser = new CmdLineParser(options);
    try {
      parser.parseArgument(args);
      ReferenceLabelsExampleProcessor processor = new ReferenceLabelsExampleProcessor();
      Server server = options.build(processor);
      server.start();
      server.blockUntilShutdown();
    } catch (IOException e) {
      System.err.println("Failed to start server: " + e.getMessage());
    } catch (InterruptedException e) {
      System.err.println("Server interrupted.");
    } catch (CmdLineException e) {
      ProcessorServer.Builder.printHelp(parser, WordOccurrencesExampleProcessor.class, e, null);
    }
  }
}
