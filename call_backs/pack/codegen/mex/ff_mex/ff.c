/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * ff.c
 *
 * Code generation for function 'ff'
 *
 */

/* Include files */
#include "ff.h"
#include "applyToMultipleDims.h"
#include "assertCompatibleDims.h"
#include "div.h"
#include "ff_mex_data.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "imgaussfilt.h"
#include "rt_nonfinite.h"
#include "omp.h"
#include <string.h>

/* Variable Definitions */
static emlrtRTEInfo hb_emlrtRTEI = {
    9,    /* lineNo */
    9,    /* colNo */
    "ff", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ff.m" /* pName */
};

static emlrtRTEInfo ib_emlrtRTEI = {
    5,    /* lineNo */
    9,    /* colNo */
    "ff", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ff.m" /* pName */
};

/* Function Definitions */
emlrtCTX emlrtGetRootTLSGlobal(void)
{
  return emlrtRootTLSGlobal;
}

void emlrtLockerFunction(EmlrtLockeeFunction aLockee, emlrtConstCTX aTLS,
                         void *aData)
{
  omp_set_lock(&emlrtLockGlobal);
  emlrtCallLockeeFunction(aLockee, aTLS, aData);
  omp_unset_lock(&emlrtLockGlobal);
}

void ff(const emlrtStack *sp, const emxArray_real32_T *image, real_T gw,
        emxArray_real32_T *corrected_image)
{
  emlrtStack b_st;
  emlrtStack c_st;
  emlrtStack st;
  int32_T i;
  const real32_T *image_data;
  real32_T *corrected_image_data;
  st.prev = sp;
  st.tls = sp->tls;
  b_st.prev = &st;
  b_st.tls = st.tls;
  c_st.prev = &b_st;
  c_st.tls = b_st.tls;
  image_data = image->data;
  /*  ff -> flat field correction */
  if (gw != 0.0) {
    int32_T loop_ub;
    real32_T x;
    real32_T y;
    st.site = &emlrtRSI;
    b_st.site = &d_emlrtRSI;
    c_st.site = &e_emlrtRSI;
    x = applyToMultipleDims(&c_st, image);
    st.site = &b_emlrtRSI;
    b_st.site = &b_emlrtRSI;
    imgaussfilt(&b_st, image, gw, corrected_image);
    b_st.site = &le_emlrtRSI;
    c_st.site = &me_emlrtRSI;
    assertCompatibleDims(&c_st, image, corrected_image);
    if ((image->size[0] == corrected_image->size[0]) &&
        (image->size[1] == corrected_image->size[1])) {
      loop_ub = image->size[0] * image->size[1];
      i = corrected_image->size[0] * corrected_image->size[1];
      corrected_image->size[0] = image->size[0];
      corrected_image->size[1] = image->size[1];
      emxEnsureCapacity_real32_T(&b_st, corrected_image, i, &ib_emlrtRTEI);
      corrected_image_data = corrected_image->data;
      for (i = 0; i < loop_ub; i++) {
        corrected_image_data[i] = image_data[i] / corrected_image_data[i];
      }
    } else {
      c_st.site = &jj_emlrtRSI;
      rdivide(&c_st, corrected_image, image);
      corrected_image_data = corrected_image->data;
    }
    st.site = &c_emlrtRSI;
    b_st.site = &d_emlrtRSI;
    c_st.site = &e_emlrtRSI;
    y = applyToMultipleDims(&c_st, corrected_image);
    x /= y;
    loop_ub = corrected_image->size[0] * corrected_image->size[1];
    for (i = 0; i < loop_ub; i++) {
      corrected_image_data[i] *= x;
    }
  } else {
    int32_T loop_ub;
    i = corrected_image->size[0] * corrected_image->size[1];
    corrected_image->size[0] = image->size[0];
    corrected_image->size[1] = image->size[1];
    emxEnsureCapacity_real32_T(sp, corrected_image, i, &hb_emlrtRTEI);
    corrected_image_data = corrected_image->data;
    loop_ub = image->size[0] * image->size[1];
    for (i = 0; i < loop_ub; i++) {
      corrected_image_data[i] = image_data[i];
    }
  }
}

/* End of code generation (ff.c) */
