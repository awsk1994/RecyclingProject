from datasets import *
from model import fc_resnet50
from prm.prm import peak_response_mapping
from losses import multilabel_soft_margin_loss
from tensorboardX import SummaryWriter
from solver import Solver
import os
import yaml, json
from utils import *
import PIL.Image
import argparse
import cv2

CONFIG = 'config_weak.yml'
KITTI_CLASS_NAMES = ['DontCare', 'Van', 'Cyclist', 'Pedestrian', 'Car', 'Truck', 'Misc', 'Tram', 'Person']    


def main(args):

    with open(args.conf, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    
    train_trans = image_transform(**config['train_transform'])
    test_trans = image_transform(**config['test_transform'])

    config['dataset'].update({'transform': train_trans,
                              'target_transform': None})
    config['dataset']['infer_only'] = True
    # dataset = pascal_voc_classification(**config['dataset'])
    dataset = classification(**config['dataset'])
    config['data_loaders']['dataset'] = dataset
    # data_loader = fetch_voc(**config['data_loaders'])
    # train_logger = SummaryWriter(log_dir = os.path.join(config['log'], 'train'), comment = 'training')
    solver = Solver(config)

    # Load demo images and pre-computed object proposals
    # change the idx to test different samples
    idx = 0
    try:
        raw_img = PIL.Image.open('./data/sample%d.png' % idx).convert('RGB')
    except:
        raw_img = PIL.Image.open('./data/sample%d.jpg' % idx).convert('RGB')
    raw_size = raw_img.size
    input_var = test_trans(raw_img).unsqueeze(0).cuda().requires_grad_()
    proposals=[]
    # proposals = list(map(rle_decode, json.load(f)))
    for i in range(10):
        proposals.append(np.genfromtxt('data/kitti/'+str(idx)+'/mask'+str(i)+'.csv', delimiter=','))
    proposals=proposals
    # print(len(np.where(proposals[2] == 1)[0]))
    
    seg_res = solver.inference(input_var, raw_img, args.model_epoch, proposals=proposals,class_names=config['dataset']['class_names'], verbose=False)
    seg_res = cv2.resize(seg_res, raw_size)
    cv2.imwrite('data/sample%d_seg.png' % idx, seg_res * 255)
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--train','-T', type=bool, default=False, help='set train mode up, default False')
    parser.add_argument('--run_demo','-D', type=bool, default=True, help='run demo, default True')
    parser.add_argument('--conf','-C', type=str, default=CONFIG, help='config file, default VOC2012')
    parser.add_argument("--model_epoch", type=int, default=-1, help='model index to be loaded for demo, default using latest with -1')
    
    args = parser.parse_args()
    main(args)
