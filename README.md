# Offline PaddleOCR

一个面向 Windows 的 PaddleOCR 本地离线部署包装项目，提供：

- 本地命令行 OCR 入口
- 本地 HTTP 服务
- CPU 独立虚拟环境
- 面向 NVIDIA 机器的 GPU 独立虚拟环境
- 可共享的本地模型缓存目录

适合这些场景：

- 需要完全离线运行 OCR
- 需要在 CPU / GPU 之间快速切换
- 需要给本地工具、脚本或其它程序提供 HTTP OCR 服务
- 不想直接处理 PaddleOCR 大仓库里的复杂组件

只要先完成一次模型预下载，后续断网也可以继续运行。

## 模型下载源

项目现在支持 3 种模型下载源：

- `modelscope`
- `huggingface`
- `aistudio`

默认下载源是：

```text
modelscope
```

也就是更适合国内网络环境的配置。

## 快速开始

在当前目录执行：

```powershell
.\prefetch_cpu.cmd
.\start_cpu.cmd
```

然后访问：

```text
http://127.0.0.1:18080/health
```

或者直接命令行识别：

```powershell
.\ocr_cpu.cmd -i .\sample.png
```

如果想临时切换下载源，例如切到 Hugging Face：

```powershell
$env:OCR_MODEL_SOURCE="huggingface"
.\prefetch_cpu.cmd
```

## 目录说明

- `app.py`
  本地 FastAPI 服务入口
- `cli.py`
  命令行入口，支持普通 OCR 和 PP-StructureV3
- `prefetch_models.py`
  首次下载并缓存模型
- `models/paddlex_cache`
  本地模型缓存目录，CPU 和 GPU 共用
- `start_cpu.cmd` / `start_gpu.cmd`
  启动本地 HTTP 服务
- `ocr_cpu.cmd` / `ocr_gpu.cmd`
  命令行执行通用 OCR
- `structure_cpu.cmd` / `structure_gpu.cmd`
  命令行执行 PP-StructureV3 版面分析
- `prefetch_cpu.cmd` / `prefetch_gpu.cmd`
  预下载模型，供离线运行使用

## 首次使用

第一次使用前，建议先下载模型缓存。

CPU 机器执行：

```powershell
.\prefetch_cpu.cmd
```

如果以后要在 NVIDIA 机器上运行，也可以执行：

```powershell
.\prefetch_gpu.cmd
```

模型下载完成后，运行时会优先使用本地缓存，不再依赖联网。

### 指定下载源

可以通过环境变量切换下载源：

```powershell
$env:OCR_MODEL_SOURCE="modelscope"
.\prefetch_cpu.cmd
```

```powershell
$env:OCR_MODEL_SOURCE="huggingface"
.\prefetch_cpu.cmd
```

```powershell
$env:OCR_MODEL_SOURCE="aistudio"
.\prefetch_cpu.cmd
```

也可以直接给底层预下载脚本传参数：

```powershell
..\..\runtime\.venv-cpu\Scripts\python.exe .\prefetch_models.py --model-source modelscope
```

```powershell
..\..\runtime\.venv-cpu\Scripts\python.exe .\prefetch_models.py --model-source huggingface
```

```powershell
..\..\runtime\.venv-cpu\Scripts\python.exe .\prefetch_models.py --model-source aistudio
```

## 运行方式总览

支持 4 种常用方式：

1. 启动本地 HTTP 服务，供其他程序调用
2. 命令行执行通用 OCR
3. 命令行执行文档版面分析
4. 直接调用 Python 脚本

## 方式一：启动本地 HTTP 服务

### CPU 服务

```powershell
.\start_cpu.cmd
```

### GPU 服务

```powershell
.\start_gpu.cmd
```

默认监听地址：

```text
http://127.0.0.1:18080
```

### 健康检查

浏览器打开：

```text
http://127.0.0.1:18080/health
```

或命令行：

```powershell
curl.exe http://127.0.0.1:18080/health
```

### 调用普通 OCR 接口

```powershell
curl.exe -X POST -F "file=@.\image.jpg" http://127.0.0.1:18080/ocr
```

指定设备也可以这样传：

```powershell
curl.exe -X POST -F "file=@.\image.jpg" -F "device=cpu" http://127.0.0.1:18080/ocr
```

如果是在有 NVIDIA 的机器上：

```powershell
curl.exe -X POST -F "file=@.\image.jpg" -F "device=gpu:0" http://127.0.0.1:18080/ocr
```

### 调用版面分析接口

```powershell
curl.exe -X POST -F "file=@.\document.png" http://127.0.0.1:18080/structure
```

指定 GPU：

```powershell
curl.exe -X POST -F "file=@.\document.png" -F "device=gpu:0" http://127.0.0.1:18080/structure
```

## 方式二：命令行执行通用 OCR

### CPU

```powershell
.\ocr_cpu.cmd -i .\image.jpg
```

### GPU

```powershell
.\ocr_gpu.cmd -i .\image.jpg
```

### 保存结果到 JSON 文件

```powershell
.\ocr_cpu.cmd -i .\image.jpg -o .\ocr_result.json
```

### 使用底层 Python CLI

```powershell
..\..\runtime\.venv-cpu\Scripts\python.exe .\cli.py ocr -i .\image.jpg
```

```powershell
..\..\runtime\.venv-gpu\Scripts\python.exe .\cli.py ocr -i .\image.jpg --device gpu:0
```

## 方式三：命令行执行 PP-StructureV3 版面分析

适合表格、文档页面、复杂版面场景。

### CPU

```powershell
.\structure_cpu.cmd -i .\document.png
```

### GPU

```powershell
.\structure_gpu.cmd -i .\document.png
```

### 保存结果到 JSON 文件

```powershell
.\structure_cpu.cmd -i .\document.png -o .\structure_result.json
```

### 使用底层 Python CLI

```powershell
..\..\runtime\.venv-cpu\Scripts\python.exe .\cli.py structure -i .\document.png
```

```powershell
..\..\runtime\.venv-gpu\Scripts\python.exe .\cli.py structure -i .\document.png --device gpu:0
```

## 方式四：直接运行 Python 服务入口

### CPU

```powershell
set OCR_DEVICE=cpu
..\..\runtime\.venv-cpu\Scripts\python.exe .\app.py
```

### GPU

```powershell
set OCR_DEVICE=gpu:0
..\..\runtime\.venv-gpu\Scripts\python.exe .\app.py
```

## CPU / GPU 切换规则

- 普通机器、核显机器、无 NVIDIA 驱动机器，使用 `*_cpu.cmd`
- 有 NVIDIA 显卡且驱动、CUDA 运行环境正常时，使用 `*_gpu.cmd`
- 两套环境彼此隔离，但共享同一个本地模型缓存目录

## 当前接口说明

### `GET /health`

返回服务状态、当前设备和本地缓存目录。

返回字段中还会包含：

- `model_source`

### `POST /ocr`

输入：

- `file`：上传图片或文档文件
- `device`：可选，示例 `cpu` 或 `gpu:0`

输出：

- `pipeline`
- `device`
- `input_path`
- `text`
- `results`

### `POST /structure`

输入：

- `file`：上传文档图片
- `device`：可选，示例 `cpu` 或 `gpu:0`

输出：

- `pipeline`
- `device`
- `input_path`
- `results`

## 说明

- 当前默认 OCR 封装走的是通用 OCR 和 `PP-StructureV3`
- 第一次预下载完成后，可以完全离线运行
- GPU 环境已经准备好，但只有在真实 NVIDIA 机器上才能完成 GPU 推理验证
