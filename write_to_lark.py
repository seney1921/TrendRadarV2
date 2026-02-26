import os
import json
import logging
from typing import List, Dict, Any

from lark_oapi import Client
from lark_oapi.api.bitable.v1 import (
    AppTableRecord,
    CreateAppTableRecordRequest,
    CreateAppTableRecordResponse,
    BatchCreateAppTableRecordRequest,
    BatchCreateAppTableRecordResponse,
    BatchCreateAppTableRecordRequestBody
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 读取环境变量
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET")
FEISHU_APP_TOKEN = os.getenv("FEISHU_APP_TOKEN")
FEISHU_TABLE_ID = os.getenv("FEISHU_TABLE_ID")

if not all([FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_APP_TOKEN, FEISHU_TABLE_ID]):
    logger.error("缺少必要的环境变量，请检查 FEISHU_APP_ID、FEISHU_APP_SECRET、FEISHU_APP_TOKEN、FEISHU_TABLE_ID 是否配置")
    exit(1)

# 初始化飞书客户端
client = Client.builder() \
    .app_id(FEISHU_APP_ID) \
    .app_secret(FEISHU_APP_SECRET) \
    .log_level(logging.WARNING) \
    .build()

def read_trends_json(file_path: str = "api/trends.json") -> List[Dict[str, Any]]:
    """读取并解析 trends.json 文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"成功读取 {len(data)} 条趋势记录")
        return data
    except FileNotFoundError:
        logger.error(f"文件 {file_path} 不存在")
        exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}")
        exit(1)

def build_records(data: List[Dict[str, Any]]) -> List[AppTableRecord]:
    """将趋势数据转换为飞书多维表格记录格式"""
    records = []
    for item in data:
        record = AppTableRecord.builder() \
            .fields({
                "平台": item.get("平台", ""),
                "标题": item.get("标题", ""),
                "热度": item.get("热度", 0)
            }) \
            .build()
        records.append(record)
    return records

def batch_write_records(records: List[AppTableRecord]) -> bool:
    """批量写入飞书多维表格"""
    try:
        request = BatchCreateAppTableRecordRequest.builder() \
            .app_token(FEISHU_APP_TOKEN) \
            .table_id(FEISHU_TABLE_ID) \
            .request_body(BatchCreateAppTableRecordRequestBody.builder()
                          .records(records)
                          .build()) \
            .build()
        response: BatchCreateAppTableRecordResponse = client.bitable.v1.app_table_record.batch_create(request)
        if response.success():
            logger.info(f"成功写入 {len(records)} 条记录到飞书多维表格")
            return True
        else:
            logger.error(f"写入失败: {response.msg}")
            return False
    except Exception as e:
        logger.error(f"批量写入异常: {e}")
        return False

def main():
    # 1. 读取 JSON
    trends_data = read_trends_json()
    if not trends_data:
        logger.warning("没有可写入的数据")
        return

    # 2. 构建记录
    records = build_records(trends_data)

    # 3. 批量写入
    success = batch_write_records(records)
    if success:
        logger.info("全部数据写入完成")
    else:
        logger.error("部分或全部数据写入失败")

if __name__ == "__main__":
    main()
