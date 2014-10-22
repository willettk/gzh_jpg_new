__credits__ = '''Written by Kyle Willett (willettk@gmail.com); adapted from code by Taro Sato, Steven Bamford, and Brooke Simmons'''

from PIL import Image as I      # Use Pillow instead of the default PIL or Image library
import numpy as np
import nw
from scipy.misc import imresize
from matplotlib import pyplot as plt
from copy import deepcopy

try:
    from astropy.io import fits
except:
    import pyfits as fits

basepath = '..'

jpg_path  = '%s/jpg_thumb/from_mosaics' % basepath
tiff_path = '%s/tiff_thumb/from_mosaics' % basepath
fits_path = '%s/fits_thumb' % basepath
#mosaic_path = '/Volumes/BDS_backup/Astro/GOODS/v1.0/images'
mosaic_path = '/Users/willettk/Astronomy/meetings/uk2014/gzh_jpg/GOODS_mosaics/goods-s'

random_fname = 'randomselect_uniformwithmag_basicinfo.fits'
goods_s_fname = 'goods_s_all.fits'
goods_n_fname = 'goods_n_all.fits'

finput_name = random_fname
ns = 's'                    # Specify 'n' for GOODS-N, 's' for GOODS-S

def make_jpeg(gal,color_scheme='bviz',desaturate=False,show_img=True,load_from_mosaic=False,mosaics=None):

    ascales,anonlinearity,npix_final,apedestal = get_image_defaults(color_scheme=color_scheme)

    input_oid = gal['UID_MOSAIC']
    id_str = 'g%s' % input_oid
    #print '----------------- %s --------------------' % id_str


    # Get the amount by which we need to resize the image
    # Consider all bands
    a_pix = max(gal['A_IMAGE_Z'], gal['A_IMAGE_I'], gal['A_IMAGE_V'], gal['A_IMAGE_B'])
    kron_r = max(gal['KRON_RADIUS_Z'], gal['KRON_RADIUS_I'], gal['KRON_RADIUS_V'], gal['KRON_RADIUS_B'])
    obj_size_pix = a_pix * kron_r

    # Scale in HST pixel size; go out to 2.5 times the Kron radius (standard aperture for SExtractor)
    img_size_hstpix = 3.5 * obj_size_pix

    # Sanity checks -- don't zoom in or out too far
    img_size_hstpix = max(img_size_hstpix, 120.)
    img_size_hstpix = min(img_size_hstpix, 1000.)
    
    resize_factor = npix_final / img_size_hstpix

    # Print re-sizing parameters to screen
    print '%s -- Semi-major axis [pix]: %f\n Kron radius [pix]: %f\n Image size [pix]: %f\n Resize factor: %f' % (id_str,a_pix, kron_r*a_pix, img_size_hstpix, resize_factor)
    '''
    if resize_factor < 1:
        # Resizing means that it has to be extracted from the mosaic image and then actually DOWNGRADED from the existing resolution
        # to fit a 424x424 image. Done automatically if extracted from mosaic.
        print '%10s - Resize factor: %.3f' % (id_str,resize_factor)
    else:
        print '%10s - no resize necessary:  %.3f' % (id_str,resize_factor)
    '''

    # Load FITS data from original GOODS mosaics

    if load_from_mosaic:
        if mosaics is None:
            osect = gal['OSECT_Z']
            with fits.open('%s/%s%s_v1.0_sc03_osect%i_drz.fits' % (mosaic_path,ns,'b',osect)) as f:      # Note: will work w/gzipped data, but MUCH slower.
                img_b = np.transpose(f[0].data)
            with fits.open('%s/%s%s_v1.0_sc03_osect%i_drz.fits' % (mosaic_path,ns,'v',osect)) as f:
                img_v = np.transpose(f[0].data)
            with fits.open('%s/%s%s_v1.0_sc03_osect%i_drz.fits' % (mosaic_path,ns,'i',osect)) as f:
                img_i = np.transpose(f[0].data)
            with fits.open('%s/%s%s_v1.0_sc03_osect%i_drz.fits' % (mosaic_path,ns,'z',osect)) as f:
                img_z = np.transpose(f[0].data)
        else:
            img_b,img_v,img_i,img_z = mosaics

        # Cut down the image to the Kron radius aperture

        xsize,ysize = img_v.shape
        xstart,ystart = gal['X_IMAGE_B'],gal['Y_IMAGE_B']
        halfbox = np.floor(img_size_hstpix/2.).astype(int)
        img_b = img_b[xstart-halfbox:xstart+halfbox,ystart-halfbox:ystart+halfbox]
        img_v = img_v[xstart-halfbox:xstart+halfbox,ystart-halfbox:ystart+halfbox]
        img_i = img_i[xstart-halfbox:xstart+halfbox,ystart-halfbox:ystart+halfbox]
        img_z = img_z[xstart-halfbox:xstart+halfbox,ystart-halfbox:ystart+halfbox]

    # Load FITS data from existing cutouts

    else:
        with fits.open('%s/%s_s%s_thumb.fits' % (fits_path,id_str,'b')) as f:
            img_b = f[0].data
        with fits.open('%s/%s_s%s_thumb.fits' % (fits_path,id_str,'v')) as f:
            img_v = f[0].data
        with fits.open('%s/%s_s%s_thumb.fits' % (fits_path,id_str,'i')) as f:
            img_i = f[0].data
        with fits.open('%s/%s_s%s_thumb.fits' % (fits_path,id_str,'z')) as f:
            img_z = f[0].data

    # Check that all image sizes and shapes match
    # If all images don't exist, return assertion error

    assert img_b.shape == img_v.shape == img_i.shape == img_z.shape, \
        'Array sizes must be the same shape\n B:%s, V:%s, I:%s, Z:%s' % \
        (img_b.shape,img_v.shape,img_i.shape,img_z.shape)

    # If one out of four images doesn't exist, just erase the color (NOT YET IMPLEMENTED)
    
    if color_scheme == 'bviz':
        rimage = img_z
        gimage = img_i
        bimage = np.array([img_b,img_v]).mean(axis=0)
    elif color_scheme == 'vz':
        rimage = img_z
        gimage = np.array([img_z,img_v]).mean(axis=0)
        bimage = img_v

    nx,ny = rimage.shape

    if load_from_mosaic:
        RGBim = np.array([np.transpose(rimage),np.transpose(gimage),np.transpose(bimage)])
    else:
        RGBim = np.array([rimage,gimage,bimage])
    
    # Use Nick Wherry's adapted IDL codes to scale and fit the image data
    RGBim = nw.scale_rgb(RGBim,scales=ascales)
    RGBim = nw.arcsinh_fit(RGBim,nonlinearity=anonlinearity)
    RGBim = nw.fit_to_box(RGBim)

    if desaturate:
        # optionally desaturate pixels that are dominated by a single
        # colour to avoid colourful speckled sky

        orig = deepcopy(RGBim)
        # Take the mean flux value between the three color bands
        a = RGBim.mean(axis=0)
        # mask pixels with no flux in any of the bands
        np.putmask(a, a == 0.0, 1.0)
        # create cube with each plane containing mean flux value
        acube = np.resize(a,(3,nx,ny))
        # scale each color to the mean, then divide by non-linearity factor
        bcube = (RGBim / acube) / anonlinearity
        # create a mask based on the weighted non-linear color values
        mask = np.array(bcube)
        # find the maximum weighted value per color
        w = np.max(mask,axis=0)
        # if the max value is greater than 1, replace with 1
        np.putmask(w, w > 1.0, 1.0)
        # invert mapping from 0 to 1.
        w = 1 - w
        # taper the weights with a sin function
        w = np.sin(w*np.pi/2.0)
        # multiply the original image by the normalized weights, add back the weighted mean flux, and [optionally] recolor strongest pixels
        #RGBim = RGBim * w + a*(1-w)
        RGBim = RGBim * w + a*(1-w) + a*(1-w)**2 * orig

    # Convert data to scaled bytes
    RGBim = (255.*RGBim).astype(int)
    RGBim = np.where(RGBim>255,255,RGBim)
    RGBim = np.where(RGBim<0,0,RGBim)

    # Add optional grey pedestal to the byte-scaled data

    RGBim += apedestal
    RGBim = np.where(RGBim>255,255,RGBim)

    R = RGBim[0,:,:]
    G = RGBim[1,:,:]
    B = RGBim[2,:,:]

    data = np.array([R.ravel(),G.ravel(),B.ravel()])
    data = np.transpose(data)
    pdata = []
    # putdata(x) does not work unless the (R,G,B) is given as tuple!!
    for each in data: 
        pdata.append(tuple(each))

    # Make Image in PIL format

    img = I.new('RGB',size=R.shape)
    img.putdata(pdata)

    # Rebin images to 424x424 pixels
    img = img.resize((424,424),I.ANTIALIAS)

    if show_img:
        img.show()

    # Save hardcopy as both JPG and TIFF
    out_jpg  = '%s/%s/goods_%s_%s_%s_thumb.jpg'  % ( jpg_path,color_scheme,ns,id_str,color_scheme)
    out_tiff = '%s/%s/goods_%s_%s_%s_thumb.tiff' % (tiff_path,color_scheme,ns,id_str,color_scheme)
    tiff_desc = {'RA':gal['ALPHA_J2000_B'],'DEC':gal['DELTA_J2000_B']}

    img.save(out_jpg,format='JPEG',quality=100)
    #img.save(out_tiff,quality=100,tiffinfo=tiff_desc)        

    return None

def run_all_images(load_from_mosaic=True):

    with fits.open('%s/%s' % (basepath,finput_name)) as f:
        finput_data = f[1].data
    
    '''
    Select only galaxies brighter than 24.5 mag in z-band. Fainter than this,
    there are almost galaxies with any visible features. Note this is 1 mag fainter than
    the limit originally used for GEMS and GOODS-N in GZ: Hubble
    '''
    mag_cut = (finput_data['MAG_BEST_Z'] <= 24.5) & (finput_data['MAGERR_BEST_Z'] < 1.)

    # Remove objects identified by GOODS pipeline as highly likely to be a star
    star_cut = (np.max([finput_data['CLASS_STAR_B'],finput_data['CLASS_STAR_V'],finput_data['CLASS_STAR_I'],finput_data['CLASS_STAR_Z']],axis=0) < 0.90) & \
        (np.mean([finput_data['CLASS_STAR_B'],finput_data['CLASS_STAR_V'],finput_data['CLASS_STAR_I'],finput_data['CLASS_STAR_Z']],axis=0) <= 0.75)

    data = finput_data[mag_cut & star_cut]
    n_imgs = 0

    # Load mosaic files only as needed to save on memory reads
    if load_from_mosaic:
        osects = np.unique(data['OSECT_Z'])
        # Loop over mosaic images
        for o in osects:
            osect_galaxies = data[data['OSECT_Z'] == o]
            # Loop over galaxies in mosaic
            for gal in osect_galaxies:
                with fits.open('%s/%s%s_v1.0_sc03_osect%i_drz.fits' % (mosaic_path,ns,'b',o)) as f:
                    img_b = np.transpose(f[0].data)
                with fits.open('%s/%s%s_v1.0_sc03_osect%i_drz.fits' % (mosaic_path,ns,'v',o)) as f:
                    img_v = np.transpose(f[0].data)
                with fits.open('%s/%s%s_v1.0_sc03_osect%i_drz.fits' % (mosaic_path,ns,'i',o)) as f:
                    img_i = np.transpose(f[0].data)
                with fits.open('%s/%s%s_v1.0_sc03_osect%i_drz.fits' % (mosaic_path,ns,'z',o)) as f:
                    img_z = np.transpose(f[0].data)

                # Make the JPEG image
                make_jpeg(gal,\
                    color_scheme='bviz',
                    desaturate=True,show_img = False,\
                    load_from_mosaic = True, mosaics = (img_b,img_v,img_i,img_z))
                '''
                make_jpeg(gal,\
                    color_scheme='vz',
                    desaturate=True,show_img = False,\
                    load_from_mosaic = True, mosaics = (img_b,img_v,img_i,img_z))
                '''
                n_imgs += 1

    # Load from FITS cutouts instead of the mosaic (faster, but zooms in too much for the largest angular size galaxies)
    else:
        for gal in finput_data:
            make_jpeg(gal,desaturate=False,show_img = False,load_from_mosaic = False)
            n_imgs += 1
    
    print 'Created %i images in JPG format.' % n_imgs
    print 'Done.'

    return None

def get_image_defaults(color_scheme='bviz'):

    # set parameters - pretty much trial and error here
    # for H (f160w), (H+J)/2, J (f125w)
    #scales= 2.0*[8, 7, 7]
    # for B,V,(I+z)/2
    #           [r  ,g , b ]
    #scales= 1.5*[22.,13.,32.]
    # for (B+V)/2, V, (I+z)/2
    #scales= 1.5*[23.,18.,23.]
    
    
    # for (B+V)/2, I, z
    if color_scheme == 'bviz':
        ascales= 1.75*np.array([45, 22, 28])
    
    
    # for V, (V+I)/2, I
    #scales= 2*[15,10,8]
    # for V, (V+z)/2, z
    #scales= 2*[15,10,8]
    #scales= 1.5*[26,22,21]
    #scales= 2.5*[16.,11.,11.]
    if color_scheme == 'vz':
        ascales= 2.5*np.array([16.,11.,11.])
        #ascales= 2.0*np.array([15,10,8])
        #ascales= 1.5*np.array([26,22,21])

    # according to Roger Griffith's program (also adapted from Hogg's)
    #scales= [1.3,1.4,1.3]
    anonlinearity= 2.5
    
    # number of pixels the final image should have (in x and y, each)
    npix_final = 424

    # Pedestal
    apedestal = 0

    return ascales,anonlinearity,npix_final,apedestal

def mosaic_vs_cutout():

    # Test to make sure images pulled from mosaic and Brooke's cutouts are identical for indexing (they are)

    with fits.open('%s/g7416_sv_thumb.fits' % fits_path) as f:
        thumbnail = f[0].data 
    with fits.open('%s/sv_v1.0_sc03_osect43_drz.fits' % mosaic_path) as f:
        mosaic = f[0].data
    with fits.open('%s/%s' % (basepath,finput_name)) as f:
        finput_data = f[1].data
    gal = finput_data[finput_data['UID_MOSAIC'] == 7416][0]

    cutout = np.transpose(mosaic)[gal['xstart']-1:gal['xend'],gal['ystart']-1:gal['yend']]

    vmin,vmax = 0.0, 0.25

    fig = plt.figure(2)
    fig.clf()
    ax1,ax2,ax3 = fig.add_subplot(131,aspect='equal'),fig.add_subplot(132,aspect='equal'),fig.add_subplot(133,aspect='equal')

    cutout_t = np.transpose(cutout)
    im1 = ax1.imshow(thumbnail,vmin=vmin,vmax=vmax)
    im2 = ax2.imshow(cutout_t,vmin=vmin,vmax=vmax)
    im3 = ax3.imshow(thumbnail - cutout_t)

    ax1.set_title('FITS thumbnail')
    ax2.set_title('Image from mosaic')
    ax3.set_title('Difference')

    fig.subplots_adjust(left=0.3)
    cbar_ax = fig.add_axes([0.15, 0.15, 0.05, 0.7])
    fig.colorbar(im1, cax=cbar_ax)

    fig.show()

    return None

def get_mosaic_defaults(uid=7416):

    with fits.open('%s/%s' % (basepath,finput_name)) as f:
        finput_data = f[1].data

    gal=finput_data[finput_data['UID_MOSAIC'] == uid][0]

    osect_z = gal['OSECT_Z']
    with fits.open('%s/s%s_v1.0_sc03_osect%i_drz.fits' % (mosaic_path,'b',osect_z)) as f:
        img_b = np.transpose(f[0].data)
    with fits.open('%s/s%s_v1.0_sc03_osect%i_drz.fits' % (mosaic_path,'v',osect_z)) as f:
        img_v = np.transpose(f[0].data)
    with fits.open('%s/s%s_v1.0_sc03_osect%i_drz.fits' % (mosaic_path,'i',osect_z)) as f:
        img_i = np.transpose(f[0].data)
    with fits.open('%s/s%s_v1.0_sc03_osect%i_drz.fits' % (mosaic_path,'z',osect_z)) as f:
        img_z = np.transpose(f[0].data)

    mosaics = (img_b,img_v,img_i,img_z)

    return mosaics

def make_webpage():

    with fits.open('%s/%s' % (basepath,finput_name)) as f:
        finput_data = f[1].data

    with open('/Users/willettk/Astronomy/meetings/uk2014/gzh_jpg/saturation_test.html','w') as f:
        for gal in finput_data:
            # Remove obvious stars
            if np.max([gal['CLASS_STAR_B'],gal['CLASS_STAR_V'],gal['CLASS_STAR_I'],gal['CLASS_STAR_Z']]) < 0.75 and np.mean([gal['CLASS_STAR_B'],gal['CLASS_STAR_V'],gal['CLASS_STAR_I'],gal['CLASS_STAR_Z']]) <= 0.75 and gal['MAG_BEST_Z'] <= 24.5:
                # Regular
                f.write('<IMG SRC="saturation_test/no_desaturation/goods_s_g%s_bviz_thumb.jpg" TITLE="GOODS-S id:%s r_e_V[pix]=%.1f mag_V=%.2f r_e_z[pix]=%.1f mag_z=%.2f">' % \
                    (gal['UID_MOSAIC'],gal['UID_MOSAIC'],gal['FLUX_RADIUS1_V'],gal['MAG_BEST_V'],gal['FLUX_RADIUS1_Z'],gal['MAG_BEST_Z']))
                # Desaturated
                f.write('<IMG SRC="saturation_test/desaturation/goods_s_g%s_bviz_thumb.jpg" TITLE="GOODS-S id:%s r_e_V[pix]=%.1f mag_V=%.2f r_e_z[pix]=%.1f mag_z=%.2f">' % \
                    (gal['UID_MOSAIC'],gal['UID_MOSAIC'],gal['FLUX_RADIUS1_V'],gal['MAG_BEST_V'],gal['FLUX_RADIUS1_Z'],gal['MAG_BEST_Z']))
                # Desaturated w/colored noise added back in 
                f.write('<IMG SRC="saturation_test/desaturation_plus_color/goods_s_g%s_bviz_thumb.jpg" TITLE="GOODS-S id:%s r_e_V[pix]=%.1f mag_V=%.2f r_e_z[pix]=%.1f mag_z=%.2f"><br>\n' % \
                    (gal['UID_MOSAIC'],gal['UID_MOSAIC'],gal['FLUX_RADIUS1_V'],gal['MAG_BEST_V'],gal['FLUX_RADIUS1_Z'],gal['MAG_BEST_Z']))

    return None

if __name__ == '__main__':

    """Test the code"""

    with fits.open('%s/%s' % (basepath,finput_name)) as f:
        finput_data = f[1].data

    make_jpeg(finput_data[finput_data['UID_MOSAIC'] == 7416][0],desaturate = False,show_img = False,load_from_mosaic = True)
