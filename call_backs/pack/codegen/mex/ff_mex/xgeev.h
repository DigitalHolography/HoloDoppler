/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * xgeev.h
 *
 * Code generation for function 'xgeev'
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
void xgeev(const emlrtStack *sp, const emxArray_creal32_T *A, int32_T *info,
           creal32_T W_data[], int32_T *W_size, emxArray_creal32_T *VR);

/* End of code generation (xgeev.h) */
