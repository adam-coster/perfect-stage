import re
from pprint import pprint as pp

def inputPlateDims():
    plateDims = {}
    plateDims['wellWidth']   = float(input( 'Well width  (mm): ' )) * 1000
    plateDims['wellHeight']  = float(input( 'Well height (mm): ' )) * 1000
    plateDims['wallWidth']   = float(input( 'Wall width  (mm): ' )) * 1000
    plateDims['wallHeight']  = float(input( 'Wall height (mm): ' )) * 1000
    plateDims['plateType']   = {'1':96,'2':384}[input( '[1] 96-well or [2] 384-well: ' )]
    plateDims['B2_top']      = float(input( 'Top  of B2 (Y, in mm): ' )) * 1000
    plateDims['B2_left']     = float(input( 'Left of B2 (X, in mm): ' )) * 1000

    saveName = input('Save filename: ')
    writePlateDims( plateDims, saveName )

    return plateDims

def writePlateDims( plateDims, fileName ):
    if not fileName:
        fileName = 'plateDims.txt'
    save = open(fileName, 'w')
    for metric in plateDims.keys():
        save.write(metric+'='+str(plateDims[metric])+'\n')
    save.close()

def getTotalRows( plateDims ):
    return {96: 8,384:16}[plateDims['plateType']]

def getTotalCols( plateDims ):
    return {96:12,384:24}[plateDims['plateType']]

def getOtherWell( plateDims ):
    """Top-left well is always B2, the 'other well' depends on plate type"""
    return {96:'G11',384:'O23'}[plateDims['plateType']]

def generateTestCoordinates( plateDims ):
    # Now have plate measurements.
    # Need to:
    # 1. Generate coordinates for wells B2 and G11/O22
    # 2. Output those coordinates in XML for NIS

    totalCols  = getTotalCols( plateDims )
    totalRows  = getTotalRows( plateDims )
    secondWell = getOtherWell( plateDims )

    wellCornersX = [ plateDims['B2_left'], plateDims['B2_left']-\
                     (plateDims['wellWidth']+plateDims['wallWidth'])*(totalCols-3)]
    wellCornersY = [ plateDims['B2_top'], plateDims['B2_top']+\
                     (plateDims['wellHeight']+plateDims['wallHeight'])*(totalRows-3)]

    for wIdx,well in enumerate(['B02',secondWell]):
        # Generate left, right, top, bottom coords
        edgeX  = wellCornersX[wIdx]
        edgeY  = wellCornersY[wIdx]
        wellW  = plateDims['wellWidth']
        wellH  = plateDims['wellHeight']
        wellXs = [edgeX, edgeX-wellW, edgeX-wellW/2, edgeX-wellW/2]
        wellYs = [edgeY+wellH/2, edgeY+wellH/2, edgeY, edgeY+wellH]

        xml = '<?xml version="1.0" encoding="UTF-16"?>'+\
              '<variant version="1.0">'+\
              '<no_name runtype="CLxListVariant">'+\
              '<bIncludeZ runtype="bool" value="false"/>'+\
              '<bPFSEnabled runtype="bool" value="true"/>'

        for frame in range(4):
            xml += '<Point' + str(frame).zfill(5) + ' runtype="NDSetupMultipointListItem">'+\
                       '<bChecked runtype="bool" value="true"/><strName runtype="CLxStringW" value="'
            xml += well + '_' + str(frame).zfill(4) + '"/>'
            xml += '<dXPosition runtype="double" value="{:.15f}"/>'.format(wellXs[frame])
            xml += '<dYPosition runtype="double" value="{:.15f}"/>'.format(wellYs[frame])
            xml += '<dZPosition runtype="double" value="{:.15f}"/>'.format(3000)
            xml += '<PFSOffset runtype="double" value="{:.15f}"/>' .format(-1.0)
            xml += '</Point' + str(frame).zfill(5) + '>'

        xml += '</no_name></variant>'

        save = open(well+'_testCoords.xml',mode='w',encoding='utf-16-le')
        save.write(xml)
        save.close()


def loadPlateDims( fileName ):
    file      =  open(fileName, 'r')
    plateDims = {}
    for line in file:
        line = line.strip()
        if line:
            plateDims[line.split('=')[0]] = float(line.split('=')[1])
    file.close()
    return plateDims

def main():

    plateDimsFile = input( 'Plate dimensions file: ' )
    if not plateDimsFile:
        plateDims = inputPlateDims()
    else:
        plateDims = loadPlateDims( plateDimsFile )

    generateTestCoordinates( plateDims )

    # Now allow user to tweak the values after observing outcomes on the scope
    while True:
        print('Now compare images from the two sets of coordinates...')
        yOffset = float(input('How far off (microns) is well '+getOtherWell( plateDims )+'in Y? '))
        xOffset = float(input('How far off (microns) is well '+getOtherWell( plateDims )+'in X? '))

        # Now tweak values of well/wall dims to compensate
        wallWidthFraction  = plateDims['wallWidth'  ]/(plateDims['wallWidth'  ]+plateDims['wellWidth'  ])
        wallHeightFraction = plateDims['wallHeight' ]/(plateDims['wallHeight' ]+plateDims['wellHeight' ])
        wellWidthFraction  = 1-wallWidthFraction
        wellHeightFraction = 1-wallHeightFraction

        colsBetween = getTotalCols(plateDims)-3
        rowsBetween = getTotalRows(plateDims)-3

        plateDims['wallWidth' ] = (plateDims['wallWidth' ]*colsBetween+xOffset*wallWidthFraction )/colsBetween
        plateDims['wallHeight'] = (plateDims['wallHeight']*rowsBetween+yOffset*wallHeightFraction)/rowsBetween
        plateDims['wellWidth' ] = (plateDims['wellWidth' ]*colsBetween+xOffset*wellWidthFraction )/colsBetween
        plateDims['wellHeight'] = (plateDims['wellHeight']*rowsBetween+yOffset*wellHeightFraction)/rowsBetween


        writePlateDims( plateDims, plateDimsFile )
        generateTestCoordinates( plateDims )

        print('Plate dimensions file overwritten.')
        print('New coordinates generated.')
        print('Re-image using new coordinates.')



if __name__ == '__main__':
    main()
