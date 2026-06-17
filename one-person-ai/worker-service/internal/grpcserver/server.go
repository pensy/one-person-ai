package grpcserver

import (
	"context"
	"log"
	"net"

	"google.golang.org/grpc"

	"github.com/onepersonai/worker/internal/executor"
	pb "github.com/onepersonai/worker/proto"
)

// Server 实现 proto 定义的 Worker 服务。
type Server struct {
	pb.UnimplementedWorkerServer
	executor *executor.Executor
}

func New(exec *executor.Executor) *Server {
	return &Server{executor: exec}
}

func (s *Server) SubmitTask(ctx context.Context, req *pb.SubmitTaskRequest) (*pb.SubmitTaskResponse, error) {
	taskID := s.executor.Submit(req.Type, req.Payload)
	log.Printf("[grpc] 提交任务 type=%v task_id=%s", req.Type, taskID)
	return &pb.SubmitTaskResponse{TaskId: taskID}, nil
}

func (s *Server) GetTaskStatus(ctx context.Context, req *pb.GetTaskStatusRequest) (*pb.TaskStatus, error) {
	status, result, ok := s.executor.Get(req.TaskId)
	if !ok {
		// 任务不存在时返回 UNSPECIFIED,调用方可据此判断
		return &pb.TaskStatus{
			TaskId: req.TaskId,
			Status: pb.TaskStatusEnum_TASK_STATUS_UNSPECIFIED,
		}, nil
	}
	return &pb.TaskStatus{
		TaskId:  req.TaskId,
		Status:  status,
		Result:  result,
	}, nil
}

// Serve 在指定端口启动 gRPC server,阻塞直到出错。
func Serve(port string, exec *executor.Executor) error {
	lis, err := net.Listen("tcp", ":"+port)
	if err != nil {
		return err
	}
	grpcServer := grpc.NewServer()
	pb.RegisterWorkerServer(grpcServer, New(exec))

	log.Printf("[grpc] Worker 服务监听 :%s", port)
	return grpcServer.Serve(lis)
}
