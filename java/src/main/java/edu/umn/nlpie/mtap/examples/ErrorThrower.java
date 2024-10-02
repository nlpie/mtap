package edu.umn.nlpie.mtap.examples;

import edu.umn.nlpie.mtap.common.JsonObjectBuilder;
import edu.umn.nlpie.mtap.common.JsonObject;
import edu.umn.nlpie.mtap.model.Event;
import edu.umn.nlpie.mtap.processing.EventProcessor;
import edu.umn.nlpie.mtap.processing.Processor;
import edu.umn.nlpie.mtap.processing.ProcessorServer;
import org.jetbrains.annotations.NotNull;

@Processor(
        "java-error-thrower"
)
public class ErrorThrower extends EventProcessor {
    @Override
    public void process(@NotNull Event event, @NotNull JsonObject params, @NotNull JsonObjectBuilder<?, ?> result) {
        throw new IllegalStateException("This is an exception.");
    }

    public static void main(String[] args) {
        ProcessorServer.hostProcessor(args, new ErrorThrower());
    }
}
