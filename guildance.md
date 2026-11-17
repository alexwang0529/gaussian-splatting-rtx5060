#
# 预处理+colmap输出+训练：运行train_images/train_video即可
# 可修改：fps，视频路径等
#
# evaluation
# 可以先预处理好数据，运行下列命令用于训练+评估
#
# python .\train.py -s .\data\test_run2 -m .\output\test_run2_eval --eval
# 留出部分图片作为测试集，训练时不使用这些图片的颜色监督，默认每 8 张留出一张的划分
#
# python .\render.py -m .\output\test_run2_eval
# 程序加载模型，从训练集和测试集的相机位置生成图片，并保存对应的真实图片，供后续比较。
#
# python .\metrics.py -m .\output\test_run2_eval
# 计算评价指标
# | 指标 | 衡量什么 | 哪个方向更好 |
# |---|---|---|
# | PSNR | 像素误差大小 | 越高越好 |
# | SSIM | 图像结构相似程度 | 越高越好 |
# | LPIPS | 基于视觉特征的感知差异 | 越低越好 |
#
# Interactive Viewers
# | 查看器 | 用途 | 程序 |
# |---|---|---|
# | Network Viewer | 连接正在运行的训练进程，观察当前训练效果 | `SIBR_remoteGaussian_app.exe` |
# | Real-Time Viewer | 加载已保存的模型，自由浏览场景 | `SIBR_gaussianViewer_app.exe` |
#
# 1、边训练边看
# python .\SIBR_remote_viewer.py -s .\data\test_run2
#
# 2、查看已经训练好的模型
# python .\SIBR_viewer.py -m .\output\test
#
# 将模型导出为普通色彩点云
# python .\export_point_cloud.py -i .
# \output\test_run2_eval\point_cloud\iteration_30000\point_cloud.ply -o .
# \output\test_run2_eval\point_cloud\iteration_30000\point_cloud_rgb.ply
#