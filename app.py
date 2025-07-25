# coding: utf-8

"""
@File   : new_app.py
@Author : Songkey
@Email  : songkey@pku.edu.cn
@Date   : 12/12/2024
@Desc   : 
"""
import os
import gradio as gr
from generator import Generator, MODEL_CONFIG
import torch

modelscope = False

VERSION_DICT_IMAGE = dict(
    HelloMemeV1='v1',
    HelloMemeV2='v2',
    HelloMemeV3='v3',
    HelloMemeV4='v4',
    HelloMemeV5='v5',
    HelloMemeV5b='v5b',
    HelloMemeV5c='v5c',
)

VERSION_DICT_VIDEO = dict(
    HelloMemeV1='v1',
    HelloMemeV2='v2',
    HelloMemeV3='v3',
    HelloMemeV4='v4',
    HelloMemeV5='v5',
)

with gr.Blocks(theme=gr.themes.Soft()) as app:
    gr.Markdown('''
        <div style="display: flex; justify-content: center; align-items: center; text-align: center;">
            <div>
                <h1>HelloMeme: Integrating Spatial Knitting Attentions to Embed High-Level and Fidelity-Rich Conditions in Diffusion Models</h1>
                <div style="display: flex; justify-content: center; align-items: center; text-align: center;">
                    <a href='https://songkey.github.io/hellomeme/'><img src='https://img.shields.io/badge/Project-HomePage-Green'></a>  &nbsp;\
                    <a href='https://github.com/HelloVision/HelloMeme'><img src='https://img.shields.io/badge/GitHub-Code-blue'></a>  &nbsp;\
                    <a href='https://arxiv.org/pdf/2410.22901'><img src='https://img.shields.io/badge/Paper-Arxiv-red'></a>  &nbsp;\
                    <a href='https://github.com/HelloVision/ComfyUI_HelloMeme'><img src='https://img.shields.io/badge/ComfyUI-UI-blue'></a>  &nbsp;\
                    <a href='https://github.com/HelloVision/HelloMeme'><img src='https://img.shields.io/github/stars/HelloVision/HelloMeme'></a>
                </div>
            </div>
        </div>
    ''')

    gen = Generator(gpu_id=0, dtype=torch.float16, sr=True, pipeline_dict_len=2, modelscope=modelscope)

    with gr.Tab("Style Transfer"):
        with gr.Row():
            ref_img = gr.Image(type="pil", label="Input Image")
            result_img1 = gr.Image(type="pil", label="Style x1")
            result_img2 = gr.Image(type="pil", label="style x2")
        exec_btn = gr.Button("Run")
        with gr.Column():
            with gr.Row():
                checkpoint = gr.Dropdown(choices=list(MODEL_CONFIG['sd15']['checkpoints'].keys()),
                                         value=list(MODEL_CONFIG['sd15']['checkpoints'].keys())[1], label="Checkpoint")
                lora = gr.Dropdown(choices=['None'] + list(MODEL_CONFIG['sd15']['loras'].keys()),
                                   value="None", label="LoRA")
            with gr.Row():
                lora_scale = gr.Slider(0.0, 10.0, 1.0, step=0.1, label="Lora Scale", interactive=True)
                version = gr.Dropdown(choices=list(VERSION_DICT_IMAGE.keys()), value="HelloMemeV5c", label="Version")
                cntrl_version = gr.Dropdown(choices=['HMControlNet1', 'HMControlNet2'], value="HMControlNet2", label="Control Version")
                stylize = gr.Dropdown(choices=['x1', 'x2'], value="x1", label="Stylize")
        with gr.Accordion("Advanced Options", open=False):
            with gr.Row():
                num_steps = gr.Slider(1, 50, 25, step=1, label="Steps")
                guidance = gr.Slider(1.0, 10.0, 1.5, step=0.1, label="Guidance", interactive=True)
            with gr.Row():
                seed = gr.Number(value=-1, label="Seed (-1 for random)")
                trans_ratio = gr.Slider(0.0, 1.0, 0.0, step=0.01, label="Trans Ratio", interactive=True)
                crop_reference = gr.Checkbox(label="Crop Reference", value=True)

        def img_gen_fnc(ref_img, num_steps, guidance, seed,
                        trans_ratio, crop_reference, cntrl_version, version, stylize, checkpoint, lora, lora_scale):

            if lora != 'None':
                tmp_lora_info = MODEL_CONFIG['sd15']['loras'][lora]
            else:
                lora_path = None

            if modelscope:
                from modelscope import snapshot_download
                checkpoint_path = snapshot_download(MODEL_CONFIG['sd15']['checkpoints'][checkpoint])
                if lora != 'None':
                    lora_path = os.path.join(snapshot_download(tmp_lora_info[0]), tmp_lora_info[1])
            else:
                from huggingface_hub import hf_hub_download
                checkpoint_path = MODEL_CONFIG['sd15']['checkpoints'][checkpoint]
                if lora != 'None':
                    lora_path = hf_hub_download(tmp_lora_info[0], filename=tmp_lora_info[1])

            res = None
            try:
                token = gen.load_pipeline("image", checkpoint_path=checkpoint_path, lora_path=lora_path, lora_scale=lora_scale,
                                        stylize=stylize, version=VERSION_DICT_IMAGE[version])
                res1 = gen.image_generate(token,
                                         ref_img,
                                         ref_img,
                                         num_steps,
                                         guidance,
                                         seed,
                                         '',
                                         '',
                                         trans_ratio,
                                         crop_reference,
                                         'cntrl1' if cntrl_version == 'HMControlNet1' else 'cntrl2',
                                         sr=True
                                        )
                res2 = gen.image_generate(token,
                                         res1,
                                         res1,
                                         num_steps,
                                         guidance,
                                         seed,
                                         '',
                                         '',
                                         trans_ratio,
                                         crop_reference,
                                         'cntrl1' if cntrl_version == 'HMControlNet1' else 'cntrl2',
                                        )
            except Exception as e:
                print(e)
            return [res1, res2]

        exec_btn.click(fn=img_gen_fnc,
                       inputs=[ref_img, num_steps, guidance, seed,
                               trans_ratio, crop_reference, cntrl_version, version, stylize, checkpoint,
                               lora, lora_scale],
                       outputs=[result_img1, result_img2],
                       api_name="Image Generation")
        gr.Examples(
            examples=[
                ['data/reference_images/toon.png', 25, 1.2, 1024,
                 0.0, True, 'HMControlNet2', 'HelloMemeV5c', 'x1',
                 list(MODEL_CONFIG['sd15']['checkpoints'].keys())[-1],
                 list(MODEL_CONFIG['sd15']['loras'].keys())[-2], 1.5],
                ['data/reference_images/chillout.jpg', 25, 1.2, 1024,
                 0.0, True, 'HMControlNet2', 'HelloMemeV5c', 'x1',
                 list(MODEL_CONFIG['sd15']['checkpoints'].keys())[-1],
                 list(MODEL_CONFIG['sd15']['loras'].keys())[-2], 1.5],
                ['data/reference_images/cg1.jpg', 25, 1.2, 1024,
                 0.0, True, 'HMControlNet2', 'HelloMemeV5c', 'x1',
                 list(MODEL_CONFIG['sd15']['checkpoints'].keys())[-1],
                 list(MODEL_CONFIG['sd15']['loras'].keys())[-2], 1.5],
                ['data/reference_images/cg2.jpg', 25, 1.2, 1024,
                 0.0, True, 'HMControlNet2', 'HelloMemeV5c', 'x1',
                 list(MODEL_CONFIG['sd15']['checkpoints'].keys())[-1],
                 list(MODEL_CONFIG['sd15']['loras'].keys())[-2], 1.5],
            ],
            fn=img_gen_fnc,
            inputs=[ref_img, num_steps, guidance, seed, trans_ratio,
                    crop_reference, cntrl_version, version, stylize, checkpoint, lora, lora_scale],
            outputs=[result_img1, result_img2],
            cache_examples=False,
        )

    with gr.Tab("Image Generation"):
        with gr.Row():
            ref_img = gr.Image(type="pil", label="Reference Image")
            drive_img = gr.Image(type="pil", label="Drive Image")
            result_img = gr.Image(type="pil", label="Generated Image")
        exec_btn = gr.Button("Run")
        with gr.Column():
            with gr.Row():
                checkpoint = gr.Dropdown(choices=list(MODEL_CONFIG['sd15']['checkpoints'].keys()),
                                         value=list(MODEL_CONFIG['sd15']['checkpoints'].keys())[1], label="Checkpoint")
                lora = gr.Dropdown(choices=['None'] + list(MODEL_CONFIG['sd15']['loras'].keys()),
                                   value="None", label="LoRA")
            with gr.Row():
                lora_scale = gr.Slider(0.0, 10.0, 1.0, step=0.1, label="Lora Scale", interactive=True)
                version = gr.Dropdown(choices=list(VERSION_DICT_IMAGE.keys()), value="HelloMemeV5", label="Version")
                cntrl_version = gr.Dropdown(choices=['HMControlNet1', 'HMControlNet2'], value="HMControlNet2", label="Control Version")
                stylize = gr.Dropdown(choices=['x1', 'x2'], value="x1", label="Stylize")
        with gr.Accordion("Advanced Options", open=False):
            with gr.Row():
                num_steps = gr.Slider(1, 50, 25, step=1, label="Steps")
                guidance = gr.Slider(1.0, 10.0, 1.5, step=0.1, label="Guidance", interactive=True)
            with gr.Row():
                seed = gr.Number(value=-1, label="Seed (-1 for random)")
                trans_ratio = gr.Slider(0.0, 1.0, 0.0, step=0.01, label="Trans Ratio", interactive=True)
                crop_reference = gr.Checkbox(label="Crop Reference", value=True)

        def img_gen_fnc(ref_img, drive_img, num_steps, guidance, seed,
                        trans_ratio, crop_reference, cntrl_version, version, stylize, checkpoint, lora, lora_scale):

            if lora != 'None':
                tmp_lora_info = MODEL_CONFIG['sd15']['loras'][lora]
            else:
                lora_path = None

            if modelscope:
                from modelscope import snapshot_download
                checkpoint_path = snapshot_download(MODEL_CONFIG['sd15']['checkpoints'][checkpoint])
                if lora != 'None':
                    lora_path = os.path.join(snapshot_download(tmp_lora_info[0]), tmp_lora_info[1])
            else:
                from huggingface_hub import hf_hub_download
                checkpoint_path = MODEL_CONFIG['sd15']['checkpoints'][checkpoint]
                if lora != 'None':
                    lora_path = hf_hub_download(tmp_lora_info[0], filename=tmp_lora_info[1])

            res = None
            try:
                token = gen.load_pipeline("image", checkpoint_path=checkpoint_path, lora_path=lora_path, lora_scale=lora_scale,
                                        stylize=stylize, version=VERSION_DICT_IMAGE[version])
                res = gen.image_generate(token,
                                         ref_img,
                                         drive_img,
                                         num_steps,
                                         guidance,
                                         seed,
                                         '',
                                         '',
                                         trans_ratio,
                                         crop_reference,
                                         'cntrl1' if cntrl_version == 'HMControlNet1' else 'cntrl2',
                                        )
            except Exception as e:
                print(e)
            return res

        exec_btn.click(fn=img_gen_fnc,
                       inputs=[ref_img, drive_img, num_steps, guidance, seed,
                               trans_ratio, crop_reference, cntrl_version, version, stylize, checkpoint,
                               lora, lora_scale],
                       outputs=result_img,
                       api_name="Image Generation")
        gr.Examples(
            examples=[
                ['data/reference_images/chillout.jpg', 'data/drive_images/yao.jpg', 25, 1.5, 1024,
                 0.0, True, 'HMControlNet2', 'HelloMemeV5', 'x1',
                 list(MODEL_CONFIG['sd15']['checkpoints'].keys())[2], list(MODEL_CONFIG['sd15']['loras'].keys())[1], 1.5],
                ['data/reference_images/firefly.jpg', 'data/drive_images/ysll.jpg', 25, 1.5, 1024,
                 0.0, True, 'HMControlNet2', 'HelloMemeV5', 'x1',
                 list(MODEL_CONFIG['sd15']['checkpoints'].keys())[1], "None", 1.5],
                ['data/reference_images/majicmix8.jpg', 'data/drive_images/hrwh.jpg', 25, 1.5, 1024,
                 0.0, True, 'HMControlNet2', 'HelloMemeV5', 'x1',
                 list(MODEL_CONFIG['sd15']['checkpoints'].keys())[1], "None", 1.5],
                ['data/reference_images/show1.jpg', 'data/drive_images/jue.jpg', 25, 1.5, 1080,
                 0.0, True, 'HMControlNet2', 'HelloMemeV5', 'x1',
                 list(MODEL_CONFIG['sd15']['checkpoints'].keys())[12], "None", 1.5],
                ['data/reference_images/show4.jpg', 'data/drive_images/hhh.jpg', 25, 1.5, 768,
                 0.0, True, 'HMControlNet2', 'HelloMemeV5', 'x1',
                 list(MODEL_CONFIG['sd15']['checkpoints'].keys())[8], "None", 1.5],
                ['data/reference_images/show6.jpg', 'data/drive_images/hrwh.jpg', 25, 1.5, 4096,
                 0.0, True, 'HMControlNet2', 'HelloMemeV5', 'x1',
                 list(MODEL_CONFIG['sd15']['checkpoints'].keys())[9], "None", 1.5],
            ],
            fn=img_gen_fnc,
            inputs=[ref_img, drive_img, num_steps, guidance, seed, trans_ratio,
                    crop_reference, cntrl_version, version, stylize, checkpoint, lora, lora_scale],
            outputs=result_img,
            cache_examples=False,
        )

    with gr.Tab("Video Generation"):
        with gr.Row():
            ref_img = gr.Image(type="pil", label="Reference Image")
            drive_video = gr.Video(label="Drive Video")
            result_video = gr.Video(autoplay=True, loop=True, label="Generated Video")
        exec_btn = gr.Button("Run")
        with gr.Column():
            with gr.Row():
                checkpoint = gr.Dropdown(choices=list(MODEL_CONFIG['sd15']['checkpoints'].keys()),
                                         value=list(MODEL_CONFIG['sd15']['checkpoints'].keys())[1], label="Checkpoint")
                lora = gr.Dropdown(choices=['None'] + list(MODEL_CONFIG['sd15']['loras'].keys()),
                                   value="None", label="LoRA")
            with gr.Row():
                lora_scale = gr.Slider(0.0, 10.0, 1.0, step=0.1, label="Lora Scale", interactive=True)
                version = gr.Dropdown(choices=list(VERSION_DICT_VIDEO.keys()), value="HelloMemeV2", label="Version")
                cntrl_version = gr.Dropdown(choices=['HMControlNet1', 'HMControlNet2'], value="HMControlNet2", label="Control Version")
                stylize = gr.Dropdown(choices=['x1', 'x2'], value="x1", label="Stylize")
        with gr.Accordion("Advanced Options", open=False):
            with gr.Row():
                num_steps = gr.Slider(1, 50, 25, step=1, label="Steps", interactive=True)
                guidance = gr.Slider(1.0, 10.0, 1.5, step=0.1, label="Guidance", interactive=True)
                patch_overlap = gr.Slider(1, 5, 4, step=1, label="Patch Overlap", interactive=True)
            with gr.Row():
                seed = gr.Number(value=-1, label="Seed (-1 for random)")
                trans_ratio = gr.Slider(0.0, 1.0, 0.0, step=0.01, label="Trans Ratio", interactive=True)
                with gr.Column():
                    crop_reference = gr.Checkbox(label="Crop Reference", value=True)
                    fps8 = gr.Checkbox(label="Use fps8", value=True)
        def video_gen_fnc(ref_img, drive_video, num_steps, guidance, seed,
                        trans_ratio, crop_reference, cntrl_version, version, stylize, patch_overlap,
                        checkpoint, lora, lora_scale, fps8):
            if lora != 'None':
                tmp_lora_info = MODEL_CONFIG['sd15']['loras'][lora]
            else:
                lora_path = None

            if modelscope:
                from modelscope import snapshot_download
                checkpoint_path = snapshot_download(MODEL_CONFIG['sd15']['checkpoints'][checkpoint])
                if lora != 'None':
                    lora_path = os.path.join(snapshot_download(tmp_lora_info[0]), tmp_lora_info[1])
            else:
                from huggingface_hub import hf_hub_download
                checkpoint_path = MODEL_CONFIG['sd15']['checkpoints'][checkpoint]
                if lora != 'None':
                    lora_path = hf_hub_download(tmp_lora_info[0], filename=tmp_lora_info[1])

            res = None
            try:
                token = gen.load_pipeline("video", checkpoint_path=checkpoint_path, lora_path=lora_path, lora_scale=lora_scale,
                                           stylize=stylize, version=VERSION_DICT_VIDEO[version])

                res = gen.video_generate(token,
                                         ref_img,
                                         drive_video,
                                         num_steps,
                                         guidance,
                                         seed,
                                         '',
                                         '',
                                         trans_ratio,
                                         crop_reference,
                                         patch_overlap,
                                         'cntrl1' if cntrl_version == 'HMControlNet1' else 'cntrl2',
                                         fps8
                                        )
            except Exception as e:
                print(e)
            return res
        exec_btn.click(fn=video_gen_fnc,
                       inputs=[ref_img, drive_video, num_steps, guidance, seed, trans_ratio,
                               crop_reference, cntrl_version, version, stylize, patch_overlap, checkpoint, lora,
                               lora_scale, fps8],
                       outputs=result_video,
                       api_name="Video Generation")
        gr.Examples(
            examples=[
                ['data/reference_images/chillout.jpg', 'data/drive_videos/nice.mp4', 25, 1.5, 1024, 0.2,
                 True, 'HMControlNet2', 'HelloMemeV5', 'x1', 4, list(MODEL_CONFIG['sd15']['checkpoints'].keys())[2],
                 list(MODEL_CONFIG['sd15']['loras'].keys())[1], 1.5, True],
                ['data/reference_images/zzj.jpg', 'data/drive_videos/jue.mp4', 25, 1.5, 1024, 0.0,
                 True, 'HMControlNet2', 'HelloMemeV5', 'x1', 4, list(MODEL_CONFIG['sd15']['checkpoints'].keys())[1],
                 "None", 1.5, True],
            ],
            fn=video_gen_fnc,
            inputs=[ref_img, drive_video, num_steps, guidance, seed, trans_ratio,
                    crop_reference, cntrl_version, version, stylize, patch_overlap, checkpoint,
                    lora, lora_scale, fps8],
            outputs=result_video,
            cache_examples=False,
        )

app.launch(inbrowser=True)