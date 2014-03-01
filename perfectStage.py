class Plate:
    def __init__( self ):
        
        self.plateType   = input('[1] 96-well or [2] 384-well? ')
        self.plateType   = (96, 384)[ int(self.plateType)+1 ]
        print()
        self.topleft_tY = input('Top left corner well, top Y (mm):    ')
        self.topleft_bY = input('Top left corner well, bottom Y (mm): ')
        self.topleft_lX = input('Top left corner well, left X (mm):   ')
        self.topleft_rX = input('Top left corner well, right X (mm):  ')
        print()
        self.botright_rX = input('Bottom right corner well, right X (mm):  ')
        self.botright_bY = input('Bottom right corner well, bottom Y (mm): ')
        print()
        self.imageWidth  = input('Image width (mm):  ')
        self.imageHeight = input('Image Height (mm): ')
        
        self.calculatePlateDims()
        
    def calculatePlateDims( self ):
        self.wellWidth  = abs(self.topleft_lX - self.topleft_rX)
        self.wellHeight = abs(self.topleft_tY - self.topleft_bY)
        self.plateWidth = abs(self.topleft_lX - self.botright_rX)
        self.plateHeight= abs(self.topleft_tY - self.botright_bY)
        
        self.cols = self.getCols()
        self.rows = self.getRows()
        
        self.wallWidth  = (self.plateWidth  - self.wellWidth )/(self.numCols - 1)
        self.wallHeight = (self.plateHeight - self.wellHeight)/(self.numRows - 1)
        
        
        
    def getCols( self ):
        return {96: 12, 384: 24}[self.plateType]
    
    def getRows( self ):
        return {96:  8, 384: 16}[self.plateType]
    
def getPlateDims():

    

def main():
    
