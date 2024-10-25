/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * eig.h
 *
 * Code generation for function 'eig'
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
void eig(const emlrtStack *sp, const emxArray_creal32_T *A,
         emxArray_creal32_T *V, emxArray_creal32_T *D);

/* End of code generation (eig.h) */
