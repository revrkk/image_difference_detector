import sys
import cv2
import random as rng
import numpy as np
from skimage.measure import compare_ssim
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog
from PyQt5.uic import loadUi

rng.seed(12345)

class MainForm(QDialog):
    def __init__(self):
        super(MainForm, self).__init__()

        loadUi('main-form.ui', self)
            
        self.image=None
        self.image2=None
        self.image_difference=None
        self.processed_image=None

        self.threshold=100
        self.No_cars=0
        
        self.lblOutputText.setText('Threshold: {0}'.format(self.threshold))
        
        self.btnLoadImage.clicked.connect(self.loadClicked)
        self.btnSaveImage.clicked.connect(self.saveClicked)
        self.btnApplyCanny.clicked.connect(self.applyCannyClicked)
        self.cannySlider.valueChanged.connect(self.cannyValueChanged)
        
    @pyqtSlot()
    def loadClicked(self):
        fname, filter=QFileDialog.getOpenFileName(self, 'Open File', 'D:\\', "Image Files (*.tif)")
        if fname:
            self.loadImage(fname)
        else:
            print('Ivalid Image')

    @pyqtSlot()
    def saveClicked(self):
        fname,filter=QFileDialog.getSaveFileName(self, 'Save File', 'D:\\', "Image Files (*.jpg)")
        if fname:
            cv2.imwrite(fname,self.processed_image)
        else:
            print('Error saving image')

    def thresh_callback(self):
        threshold = self.threshold

        ## [Canny]
        # Detect edges using Canny
        canny_output = cv2.Canny(self.image_difference, threshold, threshold * 2)
        
        ## [Canny]
        # Find contours
        contours, _ = cv2.findContours(canny_output, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        ## [allthework]
        # Approximate contours to polygons + get bounding rects and circles
        
        contours_poly = [None]*len(contours)
        boundRect = [None]*len(contours)
        centers = [None]*len(contours)
        radius = [None]*len(contours)
        for i, c in enumerate(contours):
            contours_poly[i] = cv2.approxPolyDP(c, 3, True)
            boundRect[i] = cv2.boundingRect(contours_poly[i])
            centers[i], radius[i] = cv2.minEnclosingCircle(contours_poly[i])
       
        ## [zeroMat]
        self.processed_image = np.zeros((canny_output.shape[0], canny_output.shape[1], 3), dtype=np.uint8)
    
        # Draw polygonal contour + bonding rects + circles
        for i in range(len(contours)):
            color = (rng.randint(0,256), rng.randint(0,256), rng.randint(0,256))
            cv2.drawContours(self.processed_image, contours_poly, i, color)
            cv2.rectangle(self.processed_image, (int(boundRect[i][0]), int(boundRect[i][1])), \
              (int(boundRect[i][0]+boundRect[i][2]), int(boundRect[i][1]+boundRect[i][3])), color, 2)
              
        self.lblNoOfContours.setText('No. of changes: {0}'.format(len(contours)))
        self.lblFinalThreshold.setText('Threshold: {0}'.format(self.threshold))
        self.lblCars.setText('No. of Cars detected: {}'.format(self.No_cars))
        self.displayImage(self.processed_image, 3)

    @pyqtSlot()
    def applyCannyClicked(self):
        self.thresh_callback()

    @pyqtSlot()
    def cannyValueChanged(self):
        self.threshold = self.cannySlider.value()
        self.lblOutputText.setText('Threshold: {0}'.format(self.threshold))
        if(self.image_difference is not None):
            self.thresh_callback()

    def loadImage(self, fname):
        if(self.image is None):
            self.image=cv2.imread(fname)
            self.displayImage(self.image, 1)
        else:
            self.image2=cv2.imread(fname)
            self.displayImage(self.image2, 2)

        if(self.image is not None and self.image2 is not None):
            gray1=cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY) if len(self.image.shape)>=3 else self.image
            gray2=cv2.cvtColor(self.image2, cv2.COLOR_BGR2GRAY) if len(self.image2.shape)>=3 else self.image2
            self.image_difference = cv2.absdiff(gray1, gray2)

    def displayImage(self, image, window):
        qformat=QImage.Format_Indexed8
        if len(image.shape)==3: #rows[0],cols[1],channels[2]
            if(image.shape[2])==4:
                qformat=QImage.Format_RGBA8888
            else:
                qformat=QImage.Format_RGB888
        img=QImage(image, image.shape[1],image.shape[0],image.strides[0],qformat)
        #BGR -> RGB
        img=img.rgbSwapped()        
        if window==1:
            self.lblImage.setPixmap(QPixmap.fromImage(img))
            self.lblImage.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
            self.lblImage.setScaledContents(True)
        if window==2:
            self.lblImage2.setPixmap(QPixmap.fromImage(img))
            self.lblImage2.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
            self.lblImage2.setScaledContents(True)
        if window==3:
            self.lblCannyImage.setPixmap(QPixmap.fromImage(img))
            self.lblCannyImage.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
            self.lblCannyImage.setScaledContents(True)

app=QApplication(sys.argv)
app.setStyle('Fusion')
window=MainForm()
window.show()
sys.exit(app.exec_())
