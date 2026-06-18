module github.com/onepersonai/worker

go 1.25

require (
	github.com/go-sql-driver/mysql v1.8.1
	google.golang.org/grpc v1.66.0
	google.golang.org/protobuf v1.34.1
)

require (
	filippo.io/edwards25519 v1.1.0 // indirect
	golang.org/x/net v0.26.0 // indirect
	golang.org/x/sys v0.21.0 // indirect
	golang.org/x/text v0.16.0 // indirect
	google.golang.org/genproto/googleapis/rpc v0.0.0-20240604185151-ef581f913117 // indirect
)

// proto 包是编译产物(由 scripts/gen_proto.sh 生成),用 replace 指向本地目录
replace github.com/onepersonai/worker/proto => ./proto
