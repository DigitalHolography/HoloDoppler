/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * diag.h
 *
 * Code generation for function 'diag'
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
void b_diag(const emlrtStack *sp, const emxArray_creal32_T *v,
            creal32_T d_data[], int32_T *d_size);

void diag(const emlrtStack *sp, const emxArray_real_T *v, emxArray_real_T *d);

/* End of code generation (diag.h) */
