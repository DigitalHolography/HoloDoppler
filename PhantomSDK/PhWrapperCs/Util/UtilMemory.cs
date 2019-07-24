//////////////////////////////////////////////////////////////////////////////////
//  Copyright (C) 1992-2019                                                     //
//       Vision Research Inc. (An AMETEK Company) All Rights Reserved.          //
//                                                                              //
//  The licensed information contained herein is the property of                //
//  Vision Research Inc., Wayne, NJ, USA  and is subject to change              //
//  without notice.                                                             //
//                                                                              //
//  Redistribution and use in source and binary forms, with or without          //
//  modification, are permitted with the following conditions.                  //
//                                                                              //
//  THIS SOFTWARE IS PROVIDED BY VISION RESEARCH INC ``AS IS'' AND              //
//  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE       //
//  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE  //
//  ARE DISCLAIMED.  IN NO EVENT SHALL VISION RESEARCH INC BE LIABLE            //
//  FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL  //
//  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS     //
//  OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)       //
//  HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT  //
//  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY   //
//  OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF      //
//  SUCH DAMAGE.                                                                //
//                                                                              //
//  Updates:                                                                    //
//              June 28, 2017   Updated for 770 SDK Release                     //
//                                                                              //
//////////////////////////////////////////////////////////////////////////////////

using System;
using System.Collections.Generic;
using System.Text;
using System.Runtime.InteropServices;
using System.Collections;

namespace PhSharp
{
    public static class UtilMemory
    {

        /// <summary>
        /// Turn 'cnt' elements from 'buf' into an arraylist of elements of type 'elemType'
        /// </summary>
        /// <param name="buf"></param>
        /// <param name="cnt"></param>
        /// <param name="elemType"></param>
        /// <returns>ArrayList of 'elemType' objects</returns>
        public static ArrayList MarshalByteArrayToObjectList(byte[] buf, uint cnt, Type elemType)
        {
            //List<elemType> result = new List<elemType>(); 
            ArrayList result = new ArrayList();

            int elemSize = Marshal.SizeOf(elemType);

            IntPtr ptr = Marshal.AllocHGlobal(elemSize);//alloc crt pointer            
            Object obj;
            for (int i = 0; i < cnt; i++)  //use effective count
            {
                Marshal.Copy(buf, i * elemSize, ptr, elemSize);//buf to ptr
                obj = Marshal.PtrToStructure(ptr, elemType);           //ptr to obj
                result.Add(obj);                            //add obj to list
            }
            Marshal.FreeHGlobal(ptr);
            return result;
        }


        public static float GetFloatValueFromIntPtr(IntPtr pValue)
        {
            float[] value = new float[1];
            Marshal.Copy(pValue, value, 0, 1);
            return value[0];
        }

        public static void SetFloatValueToIntPtr(float value, ref IntPtr pValue)
        {
            float[] valueArray = new float[] { value };
            Marshal.Copy(valueArray, 0, pValue, 1);
        }

        public static void CopyStringToPointerAnsi(string strSource, IntPtr strDestPtr)
        {
            IntPtr strSourcePtr = Marshal.StringToCoTaskMemAnsi(strSource);
            byte[] strArray = new byte[strSource.Length + 1];
            Marshal.Copy(strSourcePtr, strArray, 0, strArray.Length);
            //copy to destination
            Marshal.Copy(strArray, 0, strDestPtr, strArray.Length);
            Marshal.FreeCoTaskMem(strSourcePtr);
        }
    }
}
