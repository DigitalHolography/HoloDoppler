/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * _coder_ff_mex_api.c
 *
 * Code generation for function '_coder_ff_mex_api'
 *
 */

/* Include files */
#include "_coder_ff_mex_api.h"
#include "ff.h"
#include "ff_mex_data.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "m0.h"
#include "m1.h"
#include "m2.h"
#include "ri.h"
#include "rt_nonfinite.h"
#include "sf.h"
#include "sfx.h"
#include <string.h>

/* Variable Definitions */
static emlrtRTEInfo jf_emlrtRTEI = {
    1,                   /* lineNo */
    1,                   /* colNo */
    "_coder_ff_mex_api", /* fName */
    ""                   /* pName */
};

static const int32_T iv[3] = {-1, -1, -1};

/* Function Declarations */
static void b_emlrt_marshallIn(const emlrtStack *sp, const mxArray *u,
                               const emlrtMsgIdentifier *parentId,
                               emxArray_real32_T *y);

static const mxArray *b_emlrt_marshallOut(const emxArray_real32_T *u);

static real_T c_emlrt_marshallIn(const emlrtStack *sp, const mxArray *gw,
                                 const char_T *identifier);

static const mxArray *c_emlrt_marshallOut(const emlrtStack *sp,
                                          const emxArray_creal32_T *u);

static real_T d_emlrt_marshallIn(const emlrtStack *sp, const mxArray *u,
                                 const emlrtMsgIdentifier *parentId);

static void e_emlrt_marshallIn(const emlrtStack *sp, const mxArray *SH,
                               const char_T *identifier, emxArray_real32_T *y);

static void emlrt_marshallIn(const emlrtStack *sp, const mxArray *image,
                             const char_T *identifier, emxArray_real32_T *y);

static const mxArray *emlrt_marshallOut(const emxArray_real32_T *u);

static void f_emlrt_marshallIn(const emlrtStack *sp, const mxArray *u,
                               const emlrtMsgIdentifier *parentId,
                               emxArray_real32_T *y);

static void g_emlrt_marshallIn(const emlrtStack *sp,
                               const mxArray *spatial_transformation,
                               const char_T *identifier, char_T y[7]);

static void h_emlrt_marshallIn(const emlrtStack *sp, const mxArray *u,
                               const emlrtMsgIdentifier *parentId, char_T y[7]);

static void i_emlrt_marshallIn(const emlrtStack *sp, const mxArray *kernel,
                               const char_T *identifier, emxArray_creal32_T *y);

static void j_emlrt_marshallIn(const emlrtStack *sp, const mxArray *u,
                               const emlrtMsgIdentifier *parentId,
                               emxArray_creal32_T *y);

static boolean_T k_emlrt_marshallIn(const emlrtStack *sp, const mxArray *c_svd,
                                    const char_T *identifier);

static boolean_T l_emlrt_marshallIn(const emlrtStack *sp, const mxArray *u,
                                    const emlrtMsgIdentifier *parentId);

static void m_emlrt_marshallIn(const emlrtStack *sp, const mxArray *H,
                               const char_T *identifier, emxArray_creal32_T *y);

static void n_emlrt_marshallIn(const emlrtStack *sp, const mxArray *u,
                               const emlrtMsgIdentifier *parentId,
                               emxArray_creal32_T *y);

static void o_emlrt_marshallIn(const emlrtStack *sp, const mxArray *src,
                               const emlrtMsgIdentifier *msgId,
                               emxArray_real32_T *ret);

static real_T p_emlrt_marshallIn(const emlrtStack *sp, const mxArray *src,
                                 const emlrtMsgIdentifier *msgId);

static void q_emlrt_marshallIn(const emlrtStack *sp, const mxArray *src,
                               const emlrtMsgIdentifier *msgId,
                               emxArray_real32_T *ret);

static void r_emlrt_marshallIn(const emlrtStack *sp, const mxArray *src,
                               const emlrtMsgIdentifier *msgId, char_T ret[7]);

static void s_emlrt_marshallIn(const emlrtStack *sp, const mxArray *src,
                               const emlrtMsgIdentifier *msgId,
                               emxArray_creal32_T *ret);

static boolean_T t_emlrt_marshallIn(const emlrtStack *sp, const mxArray *src,
                                    const emlrtMsgIdentifier *msgId);

static void u_emlrt_marshallIn(const emlrtStack *sp, const mxArray *src,
                               const emlrtMsgIdentifier *msgId,
                               emxArray_creal32_T *ret);

/* Function Definitions */
static void b_emlrt_marshallIn(const emlrtStack *sp, const mxArray *u,
                               const emlrtMsgIdentifier *parentId,
                               emxArray_real32_T *y)
{
  o_emlrt_marshallIn(sp, emlrtAlias(u), parentId, y);
  emlrtDestroyArray(&u);
}

static const mxArray *b_emlrt_marshallOut(const emxArray_real32_T *u)
{
  static const int32_T b_iv[3] = {0, 0, 0};
  const mxArray *m;
  const mxArray *y;
  const real32_T *u_data;
  u_data = u->data;
  y = NULL;
  m = emlrtCreateNumericArray(3, (const void *)&b_iv[0], mxSINGLE_CLASS,
                              mxREAL);
  emlrtMxSetData((mxArray *)m, (void *)&u_data[0]);
  emlrtSetDimensions((mxArray *)m, &u->size[0], 3);
  emlrtAssign(&y, m);
  return y;
}

static real_T c_emlrt_marshallIn(const emlrtStack *sp, const mxArray *gw,
                                 const char_T *identifier)
{
  emlrtMsgIdentifier thisId;
  real_T y;
  thisId.fIdentifier = (const char_T *)identifier;
  thisId.fParent = NULL;
  thisId.bParentIsCell = false;
  y = d_emlrt_marshallIn(sp, emlrtAlias(gw), &thisId);
  emlrtDestroyArray(&gw);
  return y;
}

static const mxArray *c_emlrt_marshallOut(const emlrtStack *sp,
                                          const emxArray_creal32_T *u)
{
  const mxArray *m;
  const mxArray *y;
  const creal32_T *u_data;
  int32_T b_iv[3];
  u_data = u->data;
  y = NULL;
  b_iv[0] = u->size[0];
  b_iv[1] = u->size[1];
  b_iv[2] = u->size[2];
  m = emlrtCreateNumericArray(3, &b_iv[0], mxSINGLE_CLASS, mxCOMPLEX);
  emlrtExportNumericArrayR2013b((emlrtConstCTX)sp, m, (const void *)&u_data[0],
                                4);
  emlrtAssign(&y, m);
  return y;
}

static real_T d_emlrt_marshallIn(const emlrtStack *sp, const mxArray *u,
                                 const emlrtMsgIdentifier *parentId)
{
  real_T y;
  y = p_emlrt_marshallIn(sp, emlrtAlias(u), parentId);
  emlrtDestroyArray(&u);
  return y;
}

static void e_emlrt_marshallIn(const emlrtStack *sp, const mxArray *SH,
                               const char_T *identifier, emxArray_real32_T *y)
{
  emlrtMsgIdentifier thisId;
  thisId.fIdentifier = (const char_T *)identifier;
  thisId.fParent = NULL;
  thisId.bParentIsCell = false;
  f_emlrt_marshallIn(sp, emlrtAlias(SH), &thisId, y);
  emlrtDestroyArray(&SH);
}

static void emlrt_marshallIn(const emlrtStack *sp, const mxArray *image,
                             const char_T *identifier, emxArray_real32_T *y)
{
  emlrtMsgIdentifier thisId;
  thisId.fIdentifier = (const char_T *)identifier;
  thisId.fParent = NULL;
  thisId.bParentIsCell = false;
  b_emlrt_marshallIn(sp, emlrtAlias(image), &thisId, y);
  emlrtDestroyArray(&image);
}

static const mxArray *emlrt_marshallOut(const emxArray_real32_T *u)
{
  static const int32_T b_iv[2] = {0, 0};
  const mxArray *m;
  const mxArray *y;
  const real32_T *u_data;
  u_data = u->data;
  y = NULL;
  m = emlrtCreateNumericArray(2, (const void *)&b_iv[0], mxSINGLE_CLASS,
                              mxREAL);
  emlrtMxSetData((mxArray *)m, (void *)&u_data[0]);
  emlrtSetDimensions((mxArray *)m, &u->size[0], 2);
  emlrtAssign(&y, m);
  return y;
}

static void f_emlrt_marshallIn(const emlrtStack *sp, const mxArray *u,
                               const emlrtMsgIdentifier *parentId,
                               emxArray_real32_T *y)
{
  q_emlrt_marshallIn(sp, emlrtAlias(u), parentId, y);
  emlrtDestroyArray(&u);
}

static void g_emlrt_marshallIn(const emlrtStack *sp,
                               const mxArray *spatial_transformation,
                               const char_T *identifier, char_T y[7])
{
  emlrtMsgIdentifier thisId;
  thisId.fIdentifier = (const char_T *)identifier;
  thisId.fParent = NULL;
  thisId.bParentIsCell = false;
  h_emlrt_marshallIn(sp, emlrtAlias(spatial_transformation), &thisId, y);
  emlrtDestroyArray(&spatial_transformation);
}

static void h_emlrt_marshallIn(const emlrtStack *sp, const mxArray *u,
                               const emlrtMsgIdentifier *parentId, char_T y[7])
{
  r_emlrt_marshallIn(sp, emlrtAlias(u), parentId, y);
  emlrtDestroyArray(&u);
}

static void i_emlrt_marshallIn(const emlrtStack *sp, const mxArray *kernel,
                               const char_T *identifier, emxArray_creal32_T *y)
{
  emlrtMsgIdentifier thisId;
  thisId.fIdentifier = (const char_T *)identifier;
  thisId.fParent = NULL;
  thisId.bParentIsCell = false;
  j_emlrt_marshallIn(sp, emlrtAlias(kernel), &thisId, y);
  emlrtDestroyArray(&kernel);
}

static void j_emlrt_marshallIn(const emlrtStack *sp, const mxArray *u,
                               const emlrtMsgIdentifier *parentId,
                               emxArray_creal32_T *y)
{
  s_emlrt_marshallIn(sp, emlrtAlias(u), parentId, y);
  emlrtDestroyArray(&u);
}

static boolean_T k_emlrt_marshallIn(const emlrtStack *sp, const mxArray *c_svd,
                                    const char_T *identifier)
{
  emlrtMsgIdentifier thisId;
  boolean_T y;
  thisId.fIdentifier = (const char_T *)identifier;
  thisId.fParent = NULL;
  thisId.bParentIsCell = false;
  y = l_emlrt_marshallIn(sp, emlrtAlias(c_svd), &thisId);
  emlrtDestroyArray(&c_svd);
  return y;
}

static boolean_T l_emlrt_marshallIn(const emlrtStack *sp, const mxArray *u,
                                    const emlrtMsgIdentifier *parentId)
{
  boolean_T y;
  y = t_emlrt_marshallIn(sp, emlrtAlias(u), parentId);
  emlrtDestroyArray(&u);
  return y;
}

static void m_emlrt_marshallIn(const emlrtStack *sp, const mxArray *H,
                               const char_T *identifier, emxArray_creal32_T *y)
{
  emlrtMsgIdentifier thisId;
  thisId.fIdentifier = (const char_T *)identifier;
  thisId.fParent = NULL;
  thisId.bParentIsCell = false;
  n_emlrt_marshallIn(sp, emlrtAlias(H), &thisId, y);
  emlrtDestroyArray(&H);
}

static void n_emlrt_marshallIn(const emlrtStack *sp, const mxArray *u,
                               const emlrtMsgIdentifier *parentId,
                               emxArray_creal32_T *y)
{
  u_emlrt_marshallIn(sp, emlrtAlias(u), parentId, y);
  emlrtDestroyArray(&u);
}

static void o_emlrt_marshallIn(const emlrtStack *sp, const mxArray *src,
                               const emlrtMsgIdentifier *msgId,
                               emxArray_real32_T *ret)
{
  static const int32_T dims[2] = {1024, 1024};
  int32_T b_iv[2];
  int32_T i;
  const boolean_T bv[2] = {true, true};
  emlrtCheckVsBuiltInR2012b((emlrtConstCTX)sp, msgId, src, "single", false, 2U,
                            (const void *)&dims[0], &bv[0], &b_iv[0]);
  ret->allocatedSize = b_iv[0] * b_iv[1];
  i = ret->size[0] * ret->size[1];
  ret->size[0] = b_iv[0];
  ret->size[1] = b_iv[1];
  emxEnsureCapacity_real32_T(sp, ret, i, (emlrtRTEInfo *)NULL);
  ret->data = (real32_T *)emlrtMxGetData(src);
  ret->canFreeData = false;
  emlrtDestroyArray(&src);
}

static real_T p_emlrt_marshallIn(const emlrtStack *sp, const mxArray *src,
                                 const emlrtMsgIdentifier *msgId)
{
  static const int32_T dims = 0;
  real_T ret;
  emlrtCheckBuiltInR2012b((emlrtConstCTX)sp, msgId, src, "double", false, 0U,
                          (const void *)&dims);
  ret = *(real_T *)emlrtMxGetData(src);
  emlrtDestroyArray(&src);
  return ret;
}

static void q_emlrt_marshallIn(const emlrtStack *sp, const mxArray *src,
                               const emlrtMsgIdentifier *msgId,
                               emxArray_real32_T *ret)
{
  int32_T b_iv[3];
  int32_T i;
  const boolean_T bv[3] = {true, true, true};
  emlrtCheckVsBuiltInR2012b((emlrtConstCTX)sp, msgId, src, "single", false, 3U,
                            (const void *)&iv[0], &bv[0], &b_iv[0]);
  ret->allocatedSize = b_iv[0] * b_iv[1] * b_iv[2];
  i = ret->size[0] * ret->size[1] * ret->size[2];
  ret->size[0] = b_iv[0];
  ret->size[1] = b_iv[1];
  ret->size[2] = b_iv[2];
  emxEnsureCapacity_real32_T(sp, ret, i, (emlrtRTEInfo *)NULL);
  ret->data = (real32_T *)emlrtMxGetData(src);
  ret->canFreeData = false;
  emlrtDestroyArray(&src);
}

static void r_emlrt_marshallIn(const emlrtStack *sp, const mxArray *src,
                               const emlrtMsgIdentifier *msgId, char_T ret[7])
{
  static const int32_T dims[2] = {1, 7};
  emlrtCheckBuiltInR2012b((emlrtConstCTX)sp, msgId, src, "char", false, 2U,
                          (const void *)&dims[0]);
  emlrtImportCharArrayR2015b((emlrtConstCTX)sp, src, &ret[0], 7);
  emlrtDestroyArray(&src);
}

static void s_emlrt_marshallIn(const emlrtStack *sp, const mxArray *src,
                               const emlrtMsgIdentifier *msgId,
                               emxArray_creal32_T *ret)
{
  static const int32_T dims[2] = {1024, 1024};
  creal32_T *ret_data;
  int32_T b_iv[2];
  int32_T i;
  const boolean_T bv[2] = {true, true};
  emlrtCheckVsBuiltInR2012b((emlrtConstCTX)sp, msgId, src, "single", true, 2U,
                            (const void *)&dims[0], &bv[0], &b_iv[0]);
  i = ret->size[0] * ret->size[1];
  ret->size[0] = b_iv[0];
  ret->size[1] = b_iv[1];
  emxEnsureCapacity_creal32_T(sp, ret, i, (emlrtRTEInfo *)NULL);
  ret_data = ret->data;
  emlrtImportArrayR2015b((emlrtConstCTX)sp, src, &ret_data[0], 4, true);
  emlrtDestroyArray(&src);
}

static boolean_T t_emlrt_marshallIn(const emlrtStack *sp, const mxArray *src,
                                    const emlrtMsgIdentifier *msgId)
{
  static const int32_T dims = 0;
  boolean_T ret;
  emlrtCheckBuiltInR2012b((emlrtConstCTX)sp, msgId, src, "logical", false, 0U,
                          (const void *)&dims);
  ret = *emlrtMxGetLogicals(src);
  emlrtDestroyArray(&src);
  return ret;
}

static void u_emlrt_marshallIn(const emlrtStack *sp, const mxArray *src,
                               const emlrtMsgIdentifier *msgId,
                               emxArray_creal32_T *ret)
{
  creal32_T *ret_data;
  int32_T b_iv[3];
  int32_T i;
  const boolean_T bv[3] = {true, true, true};
  emlrtCheckVsBuiltInR2012b((emlrtConstCTX)sp, msgId, src, "single", true, 3U,
                            (const void *)&iv[0], &bv[0], &b_iv[0]);
  i = ret->size[0] * ret->size[1] * ret->size[2];
  ret->size[0] = b_iv[0];
  ret->size[1] = b_iv[1];
  ret->size[2] = b_iv[2];
  emxEnsureCapacity_creal32_T(sp, ret, i, (emlrtRTEInfo *)NULL);
  ret_data = ret->data;
  emlrtImportArrayR2015b((emlrtConstCTX)sp, src, &ret_data[0], 4, true);
  emlrtDestroyArray(&src);
}

void ff_api(const mxArray *const prhs[2], const mxArray **plhs)
{
  emlrtStack st = {
      NULL, /* site */
      NULL, /* tls */
      NULL  /* prev */
  };
  emxArray_real32_T *corrected_image;
  emxArray_real32_T *image;
  real_T gw;
  st.tls = emlrtRootTLSGlobal;
  emlrtHeapReferenceStackEnterFcnR2012b(&st);
  /* Marshall function inputs */
  emxInit_real32_T(&st, &image, 2, &jf_emlrtRTEI);
  image->canFreeData = false;
  emlrt_marshallIn(&st, emlrtAlias(prhs[0]), "image", image);
  gw = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[1]), "gw");
  /* Invoke the target function */
  emxInit_real32_T(&st, &corrected_image, 2, &jf_emlrtRTEI);
  ff(&st, image, gw, corrected_image);
  emxFree_real32_T(&st, &image);
  /* Marshall function outputs */
  corrected_image->canFreeData = false;
  *plhs = emlrt_marshallOut(corrected_image);
  emxFree_real32_T(&st, &corrected_image);
  emlrtHeapReferenceStackLeaveFcnR2012b(&st);
}

void m0_api(const mxArray *const prhs[6], const mxArray **plhs)
{
  emlrtStack st = {
      NULL, /* site */
      NULL, /* tls */
      NULL  /* prev */
  };
  emxArray_real32_T *M0;
  emxArray_real32_T *SH;
  real_T batch_size;
  real_T f1;
  real_T f2;
  real_T fs;
  real_T gw;
  st.tls = emlrtRootTLSGlobal;
  emlrtHeapReferenceStackEnterFcnR2012b(&st);
  /* Marshall function inputs */
  emxInit_real32_T(&st, &SH, 3, &jf_emlrtRTEI);
  SH->canFreeData = false;
  e_emlrt_marshallIn(&st, emlrtAlias(prhs[0]), "SH", SH);
  f1 = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[1]), "f1");
  f2 = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[2]), "f2");
  fs = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[3]), "fs");
  batch_size = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[4]), "batch_size");
  gw = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[5]), "gw");
  /* Invoke the target function */
  emxInit_real32_T(&st, &M0, 2, &jf_emlrtRTEI);
  m0(&st, SH, f1, f2, fs, batch_size, gw, M0);
  emxFree_real32_T(&st, &SH);
  /* Marshall function outputs */
  M0->canFreeData = false;
  *plhs = emlrt_marshallOut(M0);
  emxFree_real32_T(&st, &M0);
  emlrtHeapReferenceStackLeaveFcnR2012b(&st);
}

void m1_api(const mxArray *const prhs[6], const mxArray **plhs)
{
  emlrtStack st = {
      NULL, /* site */
      NULL, /* tls */
      NULL  /* prev */
  };
  emxArray_real32_T *M1;
  emxArray_real32_T *SH;
  const mxArray *prhs_copy_idx_0;
  real_T batch_size;
  real_T f1;
  real_T f2;
  real_T fs;
  real_T gw;
  st.tls = emlrtRootTLSGlobal;
  emlrtHeapReferenceStackEnterFcnR2012b(&st);
  prhs_copy_idx_0 = emlrtProtectR2012b(prhs[0], 0, false, -1);
  /* Marshall function inputs */
  emxInit_real32_T(&st, &SH, 3, &jf_emlrtRTEI);
  SH->canFreeData = false;
  e_emlrt_marshallIn(&st, emlrtAlias(prhs_copy_idx_0), "SH", SH);
  f1 = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[1]), "f1");
  f2 = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[2]), "f2");
  fs = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[3]), "fs");
  batch_size = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[4]), "batch_size");
  gw = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[5]), "gw");
  /* Invoke the target function */
  emxInit_real32_T(&st, &M1, 2, &jf_emlrtRTEI);
  m1(&st, SH, f1, f2, fs, batch_size, gw, M1);
  emxFree_real32_T(&st, &SH);
  /* Marshall function outputs */
  M1->canFreeData = false;
  *plhs = emlrt_marshallOut(M1);
  emxFree_real32_T(&st, &M1);
  emlrtHeapReferenceStackLeaveFcnR2012b(&st);
}

void m2_api(const mxArray *const prhs[6], const mxArray **plhs)
{
  emlrtStack st = {
      NULL, /* site */
      NULL, /* tls */
      NULL  /* prev */
  };
  emxArray_real32_T *M2;
  emxArray_real32_T *SH;
  const mxArray *prhs_copy_idx_0;
  real_T batch_size;
  real_T f1;
  real_T f2;
  real_T fs;
  real_T gw;
  st.tls = emlrtRootTLSGlobal;
  emlrtHeapReferenceStackEnterFcnR2012b(&st);
  prhs_copy_idx_0 = emlrtProtectR2012b(prhs[0], 0, false, -1);
  /* Marshall function inputs */
  emxInit_real32_T(&st, &SH, 3, &jf_emlrtRTEI);
  SH->canFreeData = false;
  e_emlrt_marshallIn(&st, emlrtAlias(prhs_copy_idx_0), "SH", SH);
  f1 = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[1]), "f1");
  f2 = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[2]), "f2");
  fs = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[3]), "fs");
  batch_size = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[4]), "batch_size");
  gw = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[5]), "gw");
  /* Invoke the target function */
  emxInit_real32_T(&st, &M2, 2, &jf_emlrtRTEI);
  m2(&st, SH, f1, f2, fs, batch_size, gw, M2);
  emxFree_real32_T(&st, &SH);
  /* Marshall function outputs */
  M2->canFreeData = false;
  *plhs = emlrt_marshallOut(M2);
  emxFree_real32_T(&st, &M2);
  emlrtHeapReferenceStackLeaveFcnR2012b(&st);
}

void ri_api(const mxArray *const prhs[8], const mxArray **plhs)
{
  emlrtStack st = {
      NULL, /* site */
      NULL, /* tls */
      NULL  /* prev */
  };
  emxArray_creal32_T *kernel;
  emxArray_real32_T *SH;
  emxArray_real32_T *frame_batch;
  real_T svd_threshold;
  real_T svdx_nb_sub_ap;
  real_T use_gpu;
  char_T spatial_transformation[7];
  boolean_T c_svd;
  boolean_T svdx;
  st.tls = emlrtRootTLSGlobal;
  emlrtHeapReferenceStackEnterFcnR2012b(&st);
  /* Marshall function inputs */
  emxInit_real32_T(&st, &frame_batch, 3, &jf_emlrtRTEI);
  frame_batch->canFreeData = false;
  e_emlrt_marshallIn(&st, emlrtAlias(prhs[0]), "frame_batch", frame_batch);
  g_emlrt_marshallIn(&st, emlrtAliasP(prhs[1]), "spatial_transformation",
                     spatial_transformation);
  emxInit_creal32_T(&st, &kernel, 2, &jf_emlrtRTEI);
  i_emlrt_marshallIn(&st, emlrtAliasP(prhs[2]), "kernel", kernel);
  c_svd = k_emlrt_marshallIn(&st, emlrtAliasP(prhs[3]), "svd");
  svdx = k_emlrt_marshallIn(&st, emlrtAliasP(prhs[4]), "svdx");
  svd_threshold =
      c_emlrt_marshallIn(&st, emlrtAliasP(prhs[5]), "svd_threshold");
  svdx_nb_sub_ap =
      c_emlrt_marshallIn(&st, emlrtAliasP(prhs[6]), "svdx_nb_sub_ap");
  use_gpu = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[7]), "use_gpu");
  /* Invoke the target function */
  emxInit_real32_T(&st, &SH, 3, &jf_emlrtRTEI);
  ri(&st, frame_batch, spatial_transformation, kernel, c_svd, svdx,
     svd_threshold, svdx_nb_sub_ap, use_gpu, SH);
  emxFree_creal32_T(&st, &kernel);
  emxFree_real32_T(&st, &frame_batch);
  /* Marshall function outputs */
  SH->canFreeData = false;
  *plhs = b_emlrt_marshallOut(SH);
  emxFree_real32_T(&st, &SH);
  emlrtHeapReferenceStackLeaveFcnR2012b(&st);
}

void sf_api(const mxArray *const prhs[2], const mxArray **plhs)
{
  emlrtStack st = {
      NULL, /* site */
      NULL, /* tls */
      NULL  /* prev */
  };
  emxArray_creal32_T *H;
  real_T threshold;
  st.tls = emlrtRootTLSGlobal;
  emlrtHeapReferenceStackEnterFcnR2012b(&st);
  /* Marshall function inputs */
  emxInit_creal32_T(&st, &H, 3, &jf_emlrtRTEI);
  m_emlrt_marshallIn(&st, emlrtAliasP(prhs[0]), "H", H);
  threshold = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[1]), "threshold");
  /* Invoke the target function */
  sf(&st, H, threshold);
  /* Marshall function outputs */
  *plhs = c_emlrt_marshallOut(&st, H);
  emxFree_creal32_T(&st, &H);
  emlrtHeapReferenceStackLeaveFcnR2012b(&st);
}

void sfx_api(const mxArray *const prhs[3], const mxArray **plhs)
{
  emlrtStack st = {
      NULL, /* site */
      NULL, /* tls */
      NULL  /* prev */
  };
  emxArray_creal32_T *H;
  real_T nb_sub_ap;
  real_T threshold;
  st.tls = emlrtRootTLSGlobal;
  emlrtHeapReferenceStackEnterFcnR2012b(&st);
  /* Marshall function inputs */
  emxInit_creal32_T(&st, &H, 3, &jf_emlrtRTEI);
  m_emlrt_marshallIn(&st, emlrtAliasP(prhs[0]), "H", H);
  threshold = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[1]), "threshold");
  nb_sub_ap = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[2]), "nb_sub_ap");
  /* Invoke the target function */
  sfx(&st, H, threshold, nb_sub_ap);
  /* Marshall function outputs */
  *plhs = c_emlrt_marshallOut(&st, H);
  emxFree_creal32_T(&st, &H);
  emlrtHeapReferenceStackLeaveFcnR2012b(&st);
}

/* End of code generation (_coder_ff_mex_api.c) */
