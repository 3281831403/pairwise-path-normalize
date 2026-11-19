# pairwise-path-normalize

## 题面

多租户共用一套存储、高峰期并发写入时，同名文件开始互相覆盖：路径只做一次 .. 替换，%2e%2e、..;/ 和多重编码照样穿越；不做 Unicode 归一，NFC 与 NFD 被当成两个文件，配额被同名绕过；大小写与尾随点空格不折叠，A.txt、a.txt、a.txt. 在 Windows 上写的是同一个文件；包含关系用 startswith 判断，/a/bc 被当成 /a/b 的子路径；缓存键直接用原始字符串，同一文件多种写法各占一份配额、审计也对不上。tenantfs/paths.py 是核心，tests/test_paths.py 15个红。要修的是：只解一次百分号编码并拒绝残留穿越段；NFC 归一后再比较；按平台语义折叠大小写与尾随点空格；按路径段判断包含关系；所有入口共用同一个 canonical key。

## 运行方式

在仓库根目录执行：

```bash
python -m pytest tests -q
```

初始失败环境必须恰好输出 `15 failed`，且不得出现 collection error、import error、syntax error 或 test error。修复后应全部通过。

## 字段表

| 字段 | 取值 |
| --- | --- |
| 所属领域 | 安全 |
| 子方向 | 漏洞检测与攻防 |
| 任务类型 | Bugfix |
| 语言/框架 | Python 3, pytest |
| 环境可复现等级 | 无外部依赖 |

## tests 不可修改

`tests/test_paths.py` 是验收契约，包含且仅包含 15 个测试。不要修改测试文件或测试断言来让测试通过；修复应发生在 `tenantfs/paths.py`。
