'''
Implementation from https://github.com/akamaster/pytorch_resnet_cifar10.

Author:
    Properly implemented ResNet-s for CIFAR10 as described in paper [1].
    The implementation and structure of this file is hugely influenced by [2]
    which is implemented for ImageNet and doesn't have option A for identity.
    Moreover, most of the implementations on the web is copy-paste from
    torchvision's resnet and has wrong number of params.
    Proper ResNet-s for CIFAR10 (for fair comparision and etc.) has following
    number of layers and parameters:
    name      | layers | params
    ResNet20  |    20  | 0.27M
    ResNet32  |    32  | 0.46M
    ResNet44  |    44  | 0.66M
    ResNet56  |    56  | 0.85M
    ResNet110 |   110  |  1.7M
    ResNet1202|  1202  | 19.4m
    which this implementation indeed has.
'''
import torch.nn as nn
import torch
import torch.nn.functional as F
import torch.nn.init as init


__all__ = [
    'ResNet', 
    'resnet20', 
    'resnet32', 
    'resnet44', 
    'resnet56', 
    'resnet110', 
    'resnet1202'
]

def _weights_init(m):
    classname = m.__class__.__name__
    if isinstance(m, nn.Linear) or isinstance(m, nn.Conv2d):
        init.kaiming_normal(m.weight)


class LambdaLayer(nn.Module):
    def __init__(self, lambd, planes):
        super(LambdaLayer, self).__init__()
        self.lambd = lambd
        self.planes = planes

    def forward(self, x):
        return self.lambd(x, self.planes)


def pad_func(x, planes):
    return F.pad(x[:, :, ::2, ::2], (0, 0, 0, 0, planes//4, planes//4), "constant", 0)


class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, in_planes, planes, stride=1):
        super(BasicBlock, self).__init__()
        self.conv1 = nn.Conv2d(
            in_planes, planes, kernel_size=3, 
            stride=stride, padding=1, bias=False
        )
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(
            planes, planes, kernel_size=3, 
            stride=1, padding=1, bias=False
        )
        self.bn2 = nn.BatchNorm2d(planes)

        self.shortcut = nn.Sequential()
        if stride != 1 or in_planes != planes:
            self.shortcut = LambdaLayer(pad_func, planes)

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += self.shortcut(x)
        out = F.relu(out)
        return out


class ResNet(nn.Module):
    def __init__(self, block, num_blocks, num_classes=10):
        super(ResNet, self).__init__()
        self.in_planes = 16

        self.conv1 = nn.Conv2d(
            3, 16, kernel_size=3, 
            stride=1, padding=1, bias=False
        )
        self.bn1 = nn.BatchNorm2d(16)
        self.layer1 = self._make_layer(block, 16, num_blocks[0], stride=1)
        self.layer2 = self._make_layer(block, 32, num_blocks[1], stride=2)
        self.layer3 = self._make_layer(block, 64, num_blocks[2], stride=2)
        self.linear = nn.Linear(64, num_classes)

        self.apply(_weights_init)

    def _make_layer(self, block, planes, num_blocks, stride):
        strides = [stride] + [1]*(num_blocks-1)
        layers = []
        for stride in strides:
            layers.append(block(self.in_planes, planes, stride))
            self.in_planes = planes * block.expansion

        return nn.Sequential(*layers)

    def forward(self, x):

        out = F.relu(self.bn1(self.conv1(x)))
        out = self.layer1(out)
        out = self.layer2(out)
        out = self.layer3(out)
        out = F.avg_pool2d(out, out.size()[3])
        out = torch.flatten(out, 1)
        out = self.linear(out)

        return out


def resnet20(num_classes=10):
    return ResNet(BasicBlock, [3, 3, 3], num_classes)


def resnet32(num_classes=10):
    return ResNet(BasicBlock, [5, 5, 5], num_classes)


def resnet44(num_classes=10):
    return ResNet(BasicBlock, [7, 7, 7], num_classes)


def resnet56(num_classes=10):
    return ResNet(BasicBlock, [9, 9, 9], num_classes)


def resnet110(num_classes=10):
    return ResNet(BasicBlock, [18, 18, 18], num_classes)


def resnet1202(num_classes=10):
    return ResNet(BasicBlock, [200, 200, 200], num_classes)
