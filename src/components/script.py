import datetime
import sys
from flask_cors import CORS
import hashlib
from os import system
import time
from PIL import Image
import imagehash
import qrcode as QR
import cv2
import base64
from imwatermark import WatermarkEncoder
from io import BytesIO
from flask import Flask,jsonify, request
from watermark import Watermark
import numpy as np
import check
import json

blockdict={}

timestamp = time.time()
app= Flask(__name__)
CORS(app)

# API Route
@app.route('/test', methods=['GET', 'POST'])
def test():
    if request.method == 'POST':
        imgPath = request.json['imgPath']
        metaPath=request.json['metaPath']
        print(imgPath)
        print(metaPath)
        with open(metaPath,"rb") as f:
           bytes = f.read()
        encoded_string = base64.b64encode(bytes)
        blockdict["copyright"]=str(encoded_string)
        blocks=request.json['blocks']
        waterMarkImage=WatermarkImage(imgPath,metaPath)
        blockdict['watermarked']=waterMarkImage.watermark_with_transparency()

        ## Decode input data to check originality
        f=open('/home/ad105/btechProject/src/abis/Storage.json')
        data=json.load(f)
        abi=data["abi"]
        blockdict['Original']=True
        for trans in blocks:
            thash=trans['hash']
            tinput=trans['input']
            output = check.decode_tx(thash,tinput,abi)
            if thash is not None and output[1] is not None and output[0] != "decode error":
                print("Encoded Input")
                print(trans)
                print("\n")
                print("Decoded Output")
                print(output)
                if json.loads(output[1])["_perceptual_hash"]==blockdict["perceptual_hash"]:
                    blockdict['Original']= False
                    blockdict['original_copyright']=json.loads(output[1])
                    break
                    
        return blockdict

        


class DCT_Watermark(Watermark):
    def __init__(self):
        self.Q = 10
        self.size = 2

    def inner_embed(self, B: np.ndarray, signature):
        sig_size = self.sig_size
        size = self.size

        w, h = B.shape[:2]
        embed_pos = [(0, 0)]
        if w > 2 * sig_size * size:
            embed_pos.append((w-sig_size*size, 0))
        if h > 2 * sig_size * size:
            embed_pos.append((0, h-sig_size*size))
        if len(embed_pos) == 3:
            embed_pos.append((w-sig_size*size, h-sig_size*size))

        for x, y in embed_pos:
            for i in range(x, x+sig_size * size, size):
                for j in range(y, y+sig_size*size, size):
                    v = np.float32(B[i:i + size, j:j + size])
                    v = cv2.dct(v)
                    v[size-1, size-1] = self.Q * \
                        signature[((i-x)//size) * sig_size + (j-y)//size]
                    v = cv2.idct(v)
                    maximum = max(v.flatten())
                    minimum = min(v.flatten())
                    if maximum > 255:
                        v = v - (maximum - 255)
                    if minimum < 0:
                        v = v - minimum
                    B[i:i+size, j:j+size] = v
        return B

    def inner_extract(self, B):
        sig_size = 100
        size = self.size

        ext_sig = np.zeros(sig_size**2, dtype=np.int)

        for i in range(0, sig_size * size, size):
            for j in range(0, sig_size * size, size):
                v = cv2.dct(np.float32(B[i:i+size, j:j+size]))
                if v[size-1, size-1] > self.Q / 2:
                    ext_sig[(i//size) * sig_size + j//size] = 1
        return [ext_sig]






class WatermarkImage:
    def __init__(self, image, metadata):
        self.timestamp = time.time()
        self.image = image
        self.metadata = metadata
        self.perceptual_hash = imagehash.phash(Image.open(image))
        with open(image,"rb") as f:
            bytes = f.read()
        self.cryptographic_hash = hashlib.sha256(bytes).hexdigest()
        # with open(metadata,"rb") as f:
           #  bytes = f.read()
        

    def _qr_code(self):
        blockdict['perceptual_hash']=str(self.perceptual_hash)
        blockdict['cryptographic_hash']=(str)(self.cryptographic_hash)
        with open(self.metadata,"r") as f:
            data = f.read().rstrip()
        info="Timestamp: " + str(self.timestamp) + "\n" + "Perceptual Hash of image: " + str(self.perceptual_hash) + "\n" + "Owner's Information: " + str(data)
        qr_code = QR.make(info)
        qr_code.save('qr_code_' + self.image)

    def watermark_with_transparency(self):
        self._qr_code()
        img=cv2.imread(self.image)
        wm=cv2.imread('qr_code_' + self.image)
        dct = DCT_Watermark()
        wmd = dct.embed(img, wm)
        cv2.imwrite("watermark_"+self.image, wmd)
        wmd= Image.open("watermark_"+self.image)
        im_file = BytesIO()
        wmd.save(im_file, format="png")
        im_bytes = im_file.getvalue()  # im_bytes: image in binary format.
        im_b64 = base64.b64encode(im_bytes)
        return str(im_b64)

        
if __name__ == "__main__":
    
    app.run(debug=True)
    
    # args = sys.argv[1:]
    # imgPath=args[0]
    #metadataPath=args[1]
    # waterMarkImage=WatermarkImage(imgPath,metadataPath)
    # waterMarkImage.watermark_with_transparency()