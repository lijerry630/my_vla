---
title: 资源清单
date: 2026-11-18
type: page
slug: resources
summary: 论文、代码与权重、数据集、评测工具的实际入口，按学习顺序排列。
---

## 论文：先读这六篇

| 年份 | 论文 | 为什么读它 | 入口 |
| --- | --- | --- | --- |
| 2022 | RT-1: Robotics Transformer | 大规模真实数据 + 动作离散化的起点 | arXiv 2212.06817 |
| 2023 | RT-2: Vision-Language-Action Models | 动作即文本 token，语义泛化的转折 | arXiv 2307.15818 |
| 2024 | Octo: An Open-Source Generalist Robot Policy | 轻量、扩散头、易微调的开源基线 | arXiv 2405.12213 |
| 2024 | OpenVLA: An Open-Source Vision-Language-Action Model | 7B 权重开源，此后所有工作的对照 | arXiv 2406.09246 |
| 2024 | π0: A Vision-Language-Action Flow Model | 流匹配动作头，高频连续控制 | arXiv 2410.24164 |
| 2026 | VLA 综述（Concepts, Progress, Applications and Challenges） | 一篇文章看全领域脉络与分类 | arXiv 2505.04769 |

找其余论文（π0.5、FAST、SmolVLA、X-VLA、MolmoAct2、G0.5）最快的办法是按标题在 arXiv 搜索，模型迭代快，直接搜比记 ID 可靠：`https://arxiv.org/search/?query=<标题关键词>&searchtype=all`

## 代码与权重

| 项目 | 入口 | 说明 |
| --- | --- | --- |
| OpenVLA | [openvla/openvla](https://github.com/openvla/openvla) | 权重在 Hugging Face 上，MIT 许可 |
| openpi（π0 / π0.5） | [Physical-Intelligence/openpi](https://github.com/Physical-Intelligence/openpi) | 训练与推理脚本齐全，含仿真评测 |
| Isaac-GR00T | [NVIDIA/Isaac-GR00T](https://github.com/NVIDIA/Isaac-GR00T) | 双系统分层，人形与跨本体 |
| LeRobot | [huggingface/lerobot](https://github.com/huggingface/lerobot) | 数据格式、训练脚本、SmolVLA |
| Octo | [octo-models/octo](https://github.com/octo-models/octo) | 小模型基线，验证闭环用 |

## 数据集

| 数据集 | 入口 | 形态 |
| --- | --- | --- |
| Open X-Embodiment | [robotics-transformer-x.github.io](https://robotics-transformer-x.github.io/) | 多本体汇总，RLDS |
| DROID | [droid-dataset.github.io](https://droid-dataset.github.io/) | 真实场景多机位，七万级轨迹 |
| 自采数据 | LeRobot 的 dataset 目录格式 | parquet + mp4，最适合本地微调 |

## 评测与仿真

| 工具 | 入口 | 用途 |
| --- | --- | --- |
| LIBERO | [Lifelong-Robot-Learning/LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO) | 四个套件，最常用的仿真评测 |
| CALVIN | [calvin.cs.uni-freiburg.de](http://calvin.cs.uni-freiburg.de/) | 长程连续指令 |
| SimplerEnv | [simpler-env/SimplerEnv](https://github.com/simpler-env/SimplerEnv) | 真实视觉回放的仿真环境 |

## 环境与工具

- 显存吃紧时优先用 bf16 + 动作分块，不要先降分辨率
- 依赖装崩了就用干净 conda 环境重建，torch 与 CUDA 版本必须对齐
- 采集数据前先量一遍端到端延迟（相机曝光 + 传输 + 推理），chunk 长度按这个定

> 所有链接都是官方仓库或论文页。若某条失效，按项目名检索即可，不必依赖这里的固定地址。
