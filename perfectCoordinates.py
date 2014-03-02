import re

class Plate:
    def __init__( self, inFile ):

        self.readPlateDimsFromFile( inFile )
        print('This script assumes that your plate dims file\n'+
              'has accurate well/wall measurements.')

        yesno = input('Do you need to re-calibrate the stage [y/n]? ').upper()
        if yesno == 'Y':
            self.B2_top  = float(input('Top  edge of B2 (mm): '))*1000
            self.B2_left = float(input('Left edge of B2 (mm): '))*1000

        self.imageWidth  = float(input('Image width  (um): '))
        self.imageHeight = float(input('Image height (um): '))
        self.frameGrid   = int(input('For an FxF image grid, F = '))

        self.makeWells()


    def readPlateDimsFromFile( self, fileName ):
        save = open( fileName, 'r' )
        data = save.read().strip().split()
        save.close()

        dims = {}
        for line in data:
            key,value = line.split('=')
            dims[ key ] = float(value)

        self.plateType  = dims['plateType'  ]
        self.wellWidth  = dims['wellWidth'  ]
        self.wellHeight = dims['wellHeight' ]
        self.wallWidth  = dims['wallWidth'  ]
        self.wallHeight = dims['wallHeight' ]
        self.B2_left    = dims['B2_left' ]
        self.B2_top     = dims['B2_top' ]

    def makeWells( self ):

        self.cols    = self.getCols()
        self.numCols = len(self.cols)
        self.rows    = self.getRows()
        self.numRows = len(self.rows)

        topleft_centerX = self.B2_left + self.wellWidth /2 + self.wallWidth
        topleft_centerY = self.B2_top  - self.wellHeight/2 - self.wallHeight

        self.col_centers = [topleft_centerX - col*(self.wellWidth +self.wallWidth ) for col in range(self.numCols)]
        self.row_centers = [topleft_centerY + row*(self.wellHeight+self.wallHeight) for row in range(self.numRows)]

        self.wells = []
        for row, rowCenter in zip( self.rows, self.row_centers ):
            for col, colCenter in zip( self.cols, self.col_centers):
                well = Well( row + str(col).zfill(2), colCenter, rowCenter, self.imageWidth, self.imageHeight, self.frameGrid )
                self.wells.append(well)
            # every other row should be flipped for snake-style imaging
            self.cols        = self.cols[::-1]
            self.col_centers = self.col_centers[::-1]


    def asXML( self, wells = None ):
        self.xml = '<?xml version="1.0" encoding="UTF-16"?>'+\
                   '<variant version="1.0">'+\
                   '<no_name runtype="CLxListVariant">'+\
                   '<bIncludeZ runtype="bool" value="false"/>'+\
                   '<bPFSEnabled runtype="bool" value="true"/>'
        pointIdx = 0
        for well in self.wells:
            if wells == None or well.name in wells:
                for frame in range(9):
                    pointXML = '<Point' + str(pointIdx).zfill(5) + ' runtype="NDSetupMultipointListItem">'+\
                               '<bChecked runtype="bool" value="true"/><strName runtype="CLxStringW" value="'
                    pointXML += well.name + '_' + str(frame).zfill(4) + '"/>'
                    pointXML += '<dXPosition runtype="double" value="{:.15f}"/>'.format(well.frameX[frame])
                    pointXML += '<dYPosition runtype="double" value="{:.15f}"/>'.format(well.frameY[frame])
                    pointXML += '<dZPosition runtype="double" value="{:.15f}"/>'.format(well.frameZ[frame])
                    pointXML += '<PFSOffset runtype="double" value="{:.15f}"/>' .format(-1.0)
                    pointXML += '</Point' + str(pointIdx).zfill(5) + '>'

                    self.xml += pointXML
                    pointIdx += 1

        self.xml += '</no_name></variant>'
        return self.xml

    def getRows( self ):
        return {96:  [chr(i) for i in range(65,73)],
                384: [chr(i) for i in range(65,81)]}[self.plateType]

    def getCols( self ):
        return {96:  [i+1 for i in range(12)],
                384: [i+1 for i in range(24)]}[self.plateType]

class Well:
    def __init__( self, name, centerX, centerY, imageWidth, imageHeight, frameGrid, z=3000 ):
        self.name        = name
        self.centerX     = centerX
        self.centerY     = centerY
        self.Z           = z
        self.imageWidth  = imageWidth
        self.imageHeight = imageHeight
        self.frameGrid   = frameGrid

        self.generateFrameCenters()

    def generateFrameCenters( self ):

        left = self.centerX + self.imageWidth *(self.frameGrid/2-.5)
        top  = self.centerY - self.imageHeight*(self.frameGrid/2-.5)

        self.frameX = [0 for i in range(self.frameGrid**2)]
        self.frameY = [0 for i in range(self.frameGrid**2)]
        self.frameZ = [0 for i in range(self.frameGrid**2)]

        frameIdx = 0
        for frameRow in range(self.frameGrid):
            for frameCol in range(self.frameGrid):
                self.frameX[ frameIdx ] = round(left - frameCol * self.imageWidth ,15)
                self.frameY[ frameIdx ] = round(top  + frameRow * self.imageHeight,15)
                self.frameZ[ frameIdx ] = round(self.Z,15)
                frameIdx += 1

def displayPlate( rows, cols, selection=[] ):
    print( ' ' + ''.join([c.rjust(2) for c in cols]) )
    for row in rows:
        line = row
        selectionsInRow = [s for s in selection if s[0] == row]
        selectionCols   = [s[1:] for s in selectionsInRow]
        for s in cols:
            if s in selectionCols:
                line += ' X'
            else:
                line += '  '
        print(line)
    return True

def expandWellInput( rows, cols, message ):
    allWells = [r+c for r in rows for c in cols]
    rawInput = input( message ).strip().upper()
    if rawInput == 'ALL': return allWells
    if rawInput == '':    return []

    wellSets = rawInput.split(' ')

    # Allowed input formats are row, row-row, col, col-col,
    # rowcol, rowcol-rowcol
    # special keywords: all
    rowColRegex = r'^([a-zA-Z]{0,1})(\d{0,2})-{0,1}([a-zA-Z]{0,1})(\d{0,2})$'
    wellSubset = []
    for wellSet in wellSets:
        if wellSet == 'ALL': return allWells

        # Break into row and column parts
        try:
            rowStart, colStart, rowEnd, colEnd = re.match(rowColRegex,wellSet).groups()
        except:
            input('Something was wrong with your input.')
            exit()


        # Fill out the missing values
        if rowEnd   == '':
            if rowStart=='':
                rowStart = rows[0]
                rowEnd   = rows[-1]
            else:
                rowEnd = rowStart

        if colEnd   == '':
            if colStart=='':
                colStart = cols[0]
                colEnd   = cols[-1]
            else:
                colEnd = colStart

        subRows = [chr(r) for r in range(ord(rowStart),ord(rowEnd)+1)]
        subCols = [str(c) for c in range(int(colStart),int(colEnd)+1)]

        subWells = [r+c for r in subRows for c in subCols if r in rows and c in cols ]
        wellSubset += subWells

    return wellSubset






def main():

    plate = Plate( input('Plate info file: ') )
    wells = expandWellInput( plate.rows, [str(c) for c in plate.cols], 'Wells to image: ' )

    print( 'The following wells were selected: ')
    displayPlate( plate.rows, [str(c) for c in plate.cols], wells )

    xml      = plate.asXML( [w[0]+w[1:].zfill(2) for w in wells])
    saveName = 'testOut.xml' #input('Save as: ')
    save     = open(saveName,mode='w',encoding='utf-16-le')
    save.write( xml )
    save.close()


if __name__ == '__main__':
    main()