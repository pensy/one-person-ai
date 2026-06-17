"""gRPC 客户端:与 Go Worker 通信,提交并查询异步任务。

Python 侧不做实际任务执行,只负责投递与状态轮询。
Worker 不可达时抛 ConnectionError,调用方需自行降级(如同步执行兜底)。
"""
import json
import logging
from typing import Any

import grpc

from config.settings import settings

logger = logging.getLogger(__name__)

# 延迟 import 生成的 gRPC stub,避免在未生成时 import 整个服务
# 生成命令见 scripts/gen_proto.sh
_stub = None
_channel = None


def _get_stub():
    """懒加载 gRPC channel 与 stub。Worker 不可达时不阻塞 import。"""
    global _stub, _channel
    if _stub is not None:
        return _stub
    try:
        from protos import worker_pb2, worker_pb2_grpc  # noqa: 生成代码
    except ImportError:
        raise RuntimeError(
            "gRPC stub 未生成。请先运行 scripts/gen_proto.sh 生成 Python 代码。"
        )
    _channel = grpc.insecure_channel(settings.WORKER_ADDR)
    _stub = worker_pb2_grpc.WorkerStub(_channel)
    return _stub


def submit_task(task_type: str, payload: dict[str, Any], timeout: float = 5.0) -> str:
    """提交任务,返回 task_id。

    Args:
        task_type: "LLM_CALL" 或 "PR_REVIEW"
        payload: 任务负载 dict,会被序列化为 JSON
        timeout: 提交超时秒数
    Returns:
        task_id 字符串
    Raises:
        ConnectionError: Worker 不可达
    """
    stub = _get_stub()
    type_map = {"LLM_CALL": 1, "PR_REVIEW": 2}
    type_val = type_map.get(task_type, 0)
    try:
        resp = stub.SubmitTask(
            _build_request(type_val, payload),
            timeout=timeout,
        )
        return resp.task_id
    except grpc.RpcError as e:
        logger.warning("提交任务到 Worker 失败(%s): %s", settings.WORKER_ADDR, e.code())
        raise ConnectionError(f"Worker 不可达: {e.code()}") from e


def get_task_status(task_id: str, timeout: float = 5.0) -> dict[str, Any]:
    """查询任务状态。

    Returns:
        {"status": "SUCCEEDED", "result": "..."}
    """
    stub = _get_stub()
    from protos import worker_pb2  # noqa
    try:
        resp = stub.GetTaskStatus(
            worker_pb2.GetTaskStatusRequest(task_id=task_id),
            timeout=timeout,
        )
    except grpc.RpcError as e:
        logger.warning("查询任务状态失败: %s", e.code())
        raise ConnectionError(f"Worker 不可达: {e.code()}") from e

    status_name = worker_pb2.TaskStatusEnum.Name(resp.status)
    return {"status": status_name, "result": resp.result}


def _build_request(type_val: int, payload: dict[str, Any]):
    from protos import worker_pb2  # noqa
    return worker_pb2.SubmitTaskRequest(
        type=type_val,
        payload=json.dumps(payload, ensure_ascii=False),
    )
