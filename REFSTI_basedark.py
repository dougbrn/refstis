import REFSTI_functions
import numpy as np
import pyfits
import glob
import sys

def hotpix( filename ):
    pass

def update_header( filename,xbin,ybin ):
    pyfits.setval( filename, 'FILENAME', value=filename )
    pyfits.setval( filename, 'FILETYPE', value='DARK IMAGE' )
    pyfits.setval( filename, 'DETECTOR', value='CCD' )
    pyfits.setval( filename, 'CCDAMP', value='ANY' )
    pyfits.setval( filename, 'CCDGAIN', value='-1' )
    pyfits.setval( filename, 'BINAXIS1', value=xbin )
    pyfits.setval( filename, 'BINAXIS2', value=ybin )
    pyfits.setval( filename, 'USEAFTER', value='' )
    pyfits.setval( filename, 'PEDIGREE', value='INFLIGHT' )
    pyfits.setval( filename, 'DESCRIP', value='Monthly superdark created by J. Ely' )
    pyfits.setval( filename, 'NEXTEND', value=3 )
    pyfits.setval( filename, 'COMMENT', value='Reference file created by the STIS DARK reference file pipeline')

def make_basedark( input_dark_list, bias_file=None, refdark_name='basedark.fits'):
    """
    1- split all raw images into their imsets
    2- join imsets together into a single file
    3- combine and cr-reject
    4- normalize to e/s by dividing by (exptime/gain)
    5- do hot pixel things
    """
    print input_dark_list

    from pyraf import iraf
    from iraf import stsdas,toolbox,imgtools,mstools
    import os

    print 'Splitting images'
    imset_count = functions.split_images( input_dark_list )

    print 'Joining images'
    msjoin_list = ','.join( [ item for item in glob.glob('*raw??.fits') ] )# if item[:9] in bias_list] )
    print msjoin_list
    joined_out = refdark_name+ '_joined' +'.fits' 
    print joined_out
    
    msjoin_file = open('msjoin.txt','w')
    msjoin_file.write( '\n'.join(msjoin_list.split(',')) )
    msjoin_file.close()
    
    iraf.msjoin( inimg='@msjoin.txt', outimg=joined_out, Stderr='dev$null')
    
    # ocrreject
    crdone = functions.bd_crreject( joined_out )
    if (not crdone):
        functions.bd_calstis( joinedfile, bias_file )

    # divide cr-rejected
    crj_filename = refdark_name + '_crj.fits'
    exptime = pyfits.getval( crj_filename, 'TEXPTIME', ext=0 )
    gain = pyfits.getval( crj_filename, 'ATODGAIN', ext=0 )
    xbin = pyfits.getval( crj_filename, 'XBIN', ext=0 )
    ybin = pyfits.getval( crj_filename, 'YBIN', ext=0 )
    
    normalize_factor = float(exptime)/gain # ensure floating point

    norm_filename = crj_filename.replace('_crj.fits','_norm.fits')
    iraf.msarith( crj_filename, '/', normalize_factor, norm_filename ,verbose=0)  

    pyfits.setval( norm_filename, 'TEXPTIME', value=1 )

    # hotpixel stuff
    iter_count,median,sigma,npx,med,mod,min,max = functions.iterate( norm_filename )
    five_sigma = median + 5*sigma
    norm_hdu = pyfits.open( norm_hdu,mode='update' )
    index = np.where( norm_hdu[ ('SCI',1) ].data >= five_sigma + .1)[0]
    norm_hdu[ ('DQ',1) ].data[index] = 16
    norm_hdu.flush()
    norm_hdu.close()

    ### Do i need any of this?
    #hot_data = pyfits.getdata( norm_filename,ext=1 )
    #np.where( hot_data > 5*median_level, hot_data - median_level, 0 )

    #median_image = norm_filename + '_med.fits'
    #iraf.median( norm_filename, median_image, xwindow=2, ywindow=2,verbose=no)
    
    #only_dark = norm_filename+'_onlydark.fits'
    #med_hdu = pyfits.getdata( median_image,ext=1 )
    
if __name__ == "__main__":
    make_basedark( glob.glob(sys.argv[1]), sys.argv[2] )

    
    
