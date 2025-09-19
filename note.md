# note

## 下载原始数据

```powershell
python .\gdc_download.py
```

## 操作

### 数据预处理

```bash
cd Data_preprocess
conda create -n AIFFPE_preprocess python=3.7
conda activate AIFFPE_preprocess
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# or
conda env create -f environment.yml
pip install torch==1.10.2+cpu torchvision==0.11.3+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html

# WSI => .h5 patches
python create_patches.py --seg --patch --stitch \
    --source ../temp/sampleB/frozen \
    --save_dir ../temp/sampleB/frozen_patches 
python create_patches.py --seg --patch --stitch \
    --source ../temp/sampleB/ffpe \
    --save_dir ../temp/sampleB/ffpe_patches
# .h5 patches => .png patches
python h52png.py  \
    --input-path ../temp/sampleB_patches/patches/ \
    --output-path ../temp/sampleB_patches_png/

# sperate train/val
# --train-thresh TRAIN_SPLIT_RATIO --test-thresh TEST_SPLIT_RATIO
python patch_discriminator.py  \
    --train-thresh 0.33 \
    --test-thresh 0.33 \
    --frozen-dir ../temp/sample/frozen_patches/patches \
    --ffpe-dir ../temp/sample/ffpe_patches/patches  \
    --output-dir ../temp/sample_disc2

```

### 训练

```bash
# --epoch_count 2 
python train.py --gpu_ids -1 \
    --batch_size 1 \
    --n_epochs 5 \
    --epoch latest \
    --save_by_iter \
    --CUT_mode CUT \
    --dataroot temp/sample_disc2 \
    --name OV001

```

### 测试

```bash
# WSI => AI-FFPE patches
    # --CUT_mode cut \
python test.py --phase test --gpu_ids -1 \
    --epoch latest \
    --name CUT \
    --model cut \
    --CUT_mode cut \
    --checkpoints_dir 'checkpoints/OV' \
    --dataroot temp/sample_disc2 \
    --results_dir temp/sample_disc2_FFPE 

#  AI-FFPE patches => AI-FFPE WSI
python stitiching.py --h5-inpath DIR_TO_H5 --preds-path DIR_TO_PREDICTED_PATCHES --output-dir DIR_TO_STITCHED_IMAGE
# .png => .tiff
python png2tiff.py --input-dir DIR_TO_PNG --output-dir DIR_TO_TIFF
```
