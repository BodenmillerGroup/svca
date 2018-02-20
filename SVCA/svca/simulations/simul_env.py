import numpy as np
from svca.models.model2 import Model2
from svca.simulations.from_real import FromRealSimulation3
from svca.models.io import *
from svca.util_functions import utils
import sys
from limix.utils.preprocess import covar_rescaling_factor_efficient
from copy import deepcopy


def run(data_dir, protein_index, cell_types_file, output_dir, env_size,
        normalisation='standard', permute=False):
    # reading all data
    ####################################################################
    expression_file = data_dir + '/expressions.txt'
    position_file = data_dir+'/positions.txt'
    protein_names, phenotypes, X = utils.read_data(expression_file,
                                                   position_file)

    protein_name = protein_names[protein_index, :]
    phenotype = phenotypes[:, protein_index]
    sel = range(phenotypes.shape[1])
    sel.remove(protein_index)
    kin_from = phenotypes[:, sel]

    # N_samples = X.shape[0]

    boot_ix = deepcopy(env_size)
    env_size = float(int(env_size)%10)/10.
    down_sampling = 1 - float(int(env_size)/10)/10.

    # down sampling
    n_sel = down_sampling * X.shape[0]
    sel = np.sort(np.random.choice(range(X.shape[0]), n_sel, replace=False))
    X = X[sel,:]
    phenotype = phenotype[sel]
    kin_from= kin_from[sel,:]
    N_samples = X.shape[0]
    # TODO select X, select phenotype, kin_from, N_samples


    # permuting cells
    if permute:
        perm = np.random.permutation(X.shape[0])
        X = X[perm, :]

    # do null simulation
    ####################################################################
    sim = FromRealSimulation3(X, phenotype, kin_from)
    Y_sim = sim.simulate(env_size=env_size)

    # run model on simulated data
    ####################################################################
    # all but env
    ####################################################################
    cterms = ['direct', 'local']
    cell_types = ['all']
    model = Model2(Y_sim, cell_types, X, norm=normalisation, oos_predictions=0., cov_terms=cterms, kin_from=kin_from)
    model.reset_params()
    model.train_gp(grid_size=10)

    file_prefix = protein_name[0] + '_' + str(boot_ix) + '_local'
    write_variance_explained(model, output_dir, file_prefix)
    write_LL(model, output_dir, file_prefix)

    ####################################################################
    # adding env
    ####################################################################
    model.add_cov(['env'])
    model.reset_params()
    model.train_gp(grid_size=10)

    file_prefix = protein_name[0] + '_' + str(boot_ix) + '_env'
    write_variance_explained(model, output_dir, file_prefix)
    write_LL(model, output_dir, file_prefix)

    ####################################################################
    # removing local
    ####################################################################
    model.rm_cov(['local'])
    model.reset_params()
    model.train_gp(grid_size=10)

    file_prefix = protein_name[0] + '_' + str(boot_ix) + 'noLocal'
    write_variance_explained(model, output_dir, file_prefix)
    write_LL(model, output_dir, file_prefix)


if __name__ == '__main__':
    data_dir = sys.argv[1]
    cell_types_file = sys.argv[2]
    output_dir = sys.argv[3]
    protein_index = int(sys.argv[4])
    bootstrap_index = sys.argv[5]
    env_size = bootstrap_index
    # env_size = 0.1 * float(bootstrap_index)

    normalisation = sys.argv[6]

    try:
        tmp = sys.argv[7]
        if tmp == 'True':
            perm=True
        else:
            perm=False
    except:
        perm=False
	#
    #
    # data_dir = '/Users/damienarnol1/Documents/local/pro/PhD/spatial/data/IMC_reprocessed_median/Cy1x7/'
    # # protein_index = 19
    # protein_index = 3 # 5
    # cell_types_file = ''
    # env_size = 3
    # output_dir = '/Users/damienarnol1/Documents/local/pro/PhD/spatial/tests/test_new_init/'
    # normalisation='quantile'
    # perm = False

    run(data_dir, protein_index, cell_types_file, output_dir, env_size, normalisation, perm)
