# This code computes the mean position of the direct image for each visit

from astropy.io import ascii, fits
from tqdm import tqdm
import os
from astropy.io import ascii
from astropy.table import QTable
from ..lib import util
from ..lib import gaussfitter
from ..lib import plots
from ..lib import manageevent as me

def run10(eventlabel, workdir, meta=None):
	"""
	Opens the direct images to determine the position of the star on the detector.
	The positions are then saved in x and y physical pixel coordinates into a new txt file called xrefyref.txt.
	"""

	print('Starting s10')

	if meta == None:
		meta = me.loadevent(workdir + '/WFC3_' + eventlabel + "_Meta_Save")

	f = open(meta.workdir + '/xrefyref.txt', 'w')						#opens file to store positions of reference pixels
	#table = QTable(names=('t_bjd', 'ivisit', 'iorbit', 'x_pos', 'y_pos')) # creates table to store positions of reference pixels

	# load in more information into meta
	meta = util.ancil(meta, s10=True)

	t_bjd = meta.t_bjd_di
	iorbit_di = meta.iorbit_di
	ivisit_di = meta.ivisit_di

	#iterate over the direct images
	for i, file in enumerate(tqdm(meta.files_di, desc='Determining Source Positions for Direct Images', ascii=True)):

		ima = fits.open(file)

		LTV1 = ima[1].header['LTV1']					#X offset to get into physical pixels
		LTV2 = ima[1].header['LTV2']					#Y offset to get to physical pixels

		dat = ima[1].data[meta.di_rmin:meta.di_rmax, meta.di_cmin:meta.di_cmax]				#cuts out stamp around the target star
		err = ima[2].data[meta.di_rmin:meta.di_rmax, meta.di_cmin:meta.di_cmax]

		plots.image_quick(ima, i, meta)

		# If the guess for the cutout is outside of the dimensions of the dataset we will do the next iteration.
		# If this wouldn't be checked for, data AND err WILL BE EMPTY AND THE GAUSSFIT WILL TERMINATE THE STAGE.
		if meta.di_rmax > ima[1].data.shape[0] or meta.di_rmax < 0:
			print('\nYour guess for di_rmax is outside of the image.')
			continue
		if meta.di_cmax > ima[1].data.shape[1] or meta.di_cmax < 0:
			print('\nYour guess for di_cmax is outside of the image.')
			continue
		if meta.di_rmin > ima[1].data.shape[0] or meta.di_rmin < 0:
			print('\nYour guess for di_rmin is outside of the image.')
			continue
		if meta.di_cmin > ima[1].data.shape[1] or meta.di_cmin < 0:
			print('\nYour guess for di_cmin is outside of the image.')
			continue

		# run the fitter
		results = gaussfitter.gaussfit(dat, err)

		if meta.save_image_plot or meta.show_image_plot:
			plots.image(dat, ima, results, i, meta)

		# save positions into a file
		# TODO: convert this txt file to an astropy table
		# TODO: instead of listing the time and positions, the visit&orbit number and positions would be better
		print(t_bjd[i], results[3]+meta.di_rmin-LTV1, results[2]+meta.di_cmin-LTV2, file=f)
		#table.add_row([t_bjd[i], results[3]+meta.di_rmin-LTV1, results[2]+meta.di_cmin-LTV2, int(ivisit_di[i]), int(iorbit_di[i])])

		ima.close()

	#ascii.write(table, meta.workdir + '/xrefyref.txt', format='ecsv', overwrite=True)
	f.close()
	# Save results
	print('Saving Metadata')
	me.saveevent(meta, meta.workdir + '/WFC3_' + meta.eventlabel + "_Meta_Save", save=[])

	print('Finished s10 \n')

	return meta
