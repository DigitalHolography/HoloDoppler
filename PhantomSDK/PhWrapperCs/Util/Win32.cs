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
//              July 20, 2017   Updated for 770 SDK Release                     //
//                                                                              //
//////////////////////////////////////////////////////////////////////////////////

using System;
using System.Collections.Generic;
using System.Text;
using System.Runtime.InteropServices;

namespace PhSharp
{

    public enum biCompression : uint
    {
        BI_RGB = 0,
        BI_PACKED = 256     // my add to Microsoft biCompression/BITMAPINFOHEADER constants
                            // define a bitmap >8 bits as packed in the Phantom cameras
                            // (same as GI_PACKED)
    }


    [StructLayout(LayoutKind.Sequential, Pack = 1)]
    public struct BitmapFileHeader
    {
        [MarshalAs(UnmanagedType.U2)]
        public UInt16 bfType;       // ascii BM
        [MarshalAs(UnmanagedType.U4)]
        public UInt32 bfSize;       // size of bitmap in bytes
        [MarshalAs(UnmanagedType.U2)]
        public UInt16 bfReserved1;
        [MarshalAs(UnmanagedType.U2)]
        public UInt16 bfReserved2;
        [MarshalAs(UnmanagedType.U4)]
        public UInt32 bfOffBits;    // offset from start of file to bitmap bits
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct Bmi
    {
        public Bmih bmih;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 256 * 4)]
        public byte[] Colors; //dummy
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct Bmih
    {
        public uint biSize;
        public int biWidth;
        public int biHeight;
        public ushort biPlanes;
        public ushort biBitCount;
        public uint biCompression;
        public uint biSizeImage;
        public int biXPelsPerMeter;
        public int biYPelsPerMeter;
        public uint biClrUsed;
        public uint biClrImportant;

        public override bool Equals(object obj)
        {
            Bmih bmih = (Bmih)obj;
            bool isEqual = this.biBitCount == bmih.biBitCount
                            && this.biClrImportant == bmih.biClrImportant
                            && this.biClrUsed == bmih.biClrUsed
                            && this.biCompression == bmih.biCompression
                            && this.biHeight == bmih.biHeight
                            && this.biPlanes == bmih.biPlanes
                            && this.biSize == bmih.biSize
                            && this.biSizeImage == bmih.biSizeImage
                            && this.biWidth == bmih.biWidth
                            && this.biXPelsPerMeter == bmih.biXPelsPerMeter
                            && this.biYPelsPerMeter == bmih.biYPelsPerMeter;
            return isEqual;
        }

        public override int GetHashCode()
        {
            return base.GetHashCode();
        }
    }


}
