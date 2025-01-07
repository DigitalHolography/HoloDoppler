/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * ri.h
 *
 * Code generation for function 'ri'
 *
 */

#pragma once

/* Include files */
#include "ff_mex_types.h"
#include "rtwtypes.h"
#include "emlrt.h"
#include "mex.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Function Declarations */
void ri(const emlrtStack *sp, const emxArray_real32_T *frame_batch,
        const char_T spatial_transformation[7],
        const emxArray_creal32_T *kernel, boolean_T c_svd, boolean_T svdx,
        real_T svd_threshold, real_T svdx_nb_sub_ap, real_T use_gpu,
        emxArray_real32_T *SH);

/* End of code generation (ri.h) */
