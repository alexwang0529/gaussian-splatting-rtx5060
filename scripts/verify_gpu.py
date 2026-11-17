import sys, math, torch
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from simple_knn._C import distCUDA2
from fused_ssim import fused_ssim
from diff_gaussian_rasterization import GaussianRasterizationSettings, GaussianRasterizer
from utils.graphics_utils import getProjectionMatrix
import cv2, joblib
print('Python:', sys.executable)
print('PyTorch:', torch.__version__, 'CUDA:', torch.version.cuda)
print('GPU:', torch.cuda.get_device_name(0))
points = torch.tensor([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[1.,1.,0.]], device='cuda')
d = distCUDA2(points)
assert torch.allclose(d, torch.full_like(d,4./3.), atol=1e-4), d
print('PASS KNN GPU distances')
x = torch.rand((1,3,32,32),device='cuda',requires_grad=True)
y = torch.rand_like(x)
s = fused_ssim(x,y)
s.backward()
assert torch.isfinite(s).item() and torch.isfinite(x.grad).all().item()
print('PASS fused SSIM GPU forward/backward')
means = torch.tensor([[0.05,0.02,2.]],device='cuda',requires_grad=True)
means2d = torch.zeros_like(means,requires_grad=True)
colors = torch.tensor([[0.8,0.3,0.1]],device='cuda',requires_grad=True)
scales = torch.full((1,3),0.15,device='cuda',requires_grad=True)
rotations = torch.tensor([[1.,0.,0.,0.]],device='cuda',requires_grad=True)
opacity = torch.tensor([[0.8]],device='cuda',requires_grad=True)
for aa in (False, True):
    settings = GaussianRasterizationSettings(image_height=32,image_width=32,tanfovx=1.,tanfovy=1.,bg=torch.zeros(3,device='cuda'),scale_modifier=1.,viewmatrix=torch.eye(4,device='cuda'),projmatrix=getProjectionMatrix(0.01,100.,math.pi/2,math.pi/2).transpose(0,1).contiguous().cuda(),sh_degree=0,campos=torch.zeros(3,device='cuda'),prefiltered=False,debug=False,antialiasing=aa)
    rasterizer=GaussianRasterizer(settings)
    image,radii,depth=rasterizer(means3D=means,means2D=means2d,opacities=opacity,colors_precomp=colors,scales=scales,rotations=rotations)
    assert image.shape==(3,32,32) and radii[0].item()>0 and image.max().item()>0
    (image.mean()+depth.mean()).backward()
    for name,tensor in [('means',means),('colors',colors),('scales',scales),('rotations',rotations),('opacity',opacity)]:
        assert tensor.grad is not None and torch.isfinite(tensor.grad).all().item(), name
        tensor.grad=None
    means2d.grad=None
    print('PASS rasterizer GPU forward/backward; antialiasing:',aa)
torch.cuda.synchronize()
import train
print('PASS training module import; fused SSIM:', train.FUSED_SSIM_AVAILABLE)
print('ALL GPU CHECKS PASSED')
