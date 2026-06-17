module github.com/onepersonai/worker

go 1.25

require (
	google.golang.org/grpc v1.66.0
	google.golang.org/protobuf v1.34.1
)

// proto 包是编译产物(由 scripts/gen_proto.sh 生成),用 replace 指向本地目录
replace github.com/onepersonai/worker/proto => ./proto
