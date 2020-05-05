package edu.umn.nlpie.mtap.processing;

import edu.umn.nlpie.mtap.api.v1.Processing;
import io.grpc.stub.StreamObserver;

import java.io.Closeable;
import java.net.UnknownHostException;

public interface ProcessorService extends io.grpc.BindableService, AutoCloseable {
  void started(int port) throws UnknownHostException;

  void process(
      Processing.ProcessRequest request,
      StreamObserver<Processing.ProcessResponse> responseObserver
  );

  void getInfo(
      Processing.GetInfoRequest request,
      StreamObserver<Processing.GetInfoResponse> responseObserver
  );

  void getStats(
      Processing.GetStatsRequest request,
      StreamObserver<Processing.GetStatsResponse> responseObserver
  );

  @Override
  void close() throws InterruptedException;
}
