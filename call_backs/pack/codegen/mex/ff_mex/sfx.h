/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * sfx.h
 *
 * Code generation for function 'sfx'
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
void b_sfx(const emlrtStack *sp, emxArray_creal32_T *H, real_T threshold,
           real_T nb_sub_ap);

void sfx(const emlrtStack *sp, emxArray_creal32_T *H, real_T threshold,
         real_T nb_sub_ap);

/* End of code generation (sfx.h) */
