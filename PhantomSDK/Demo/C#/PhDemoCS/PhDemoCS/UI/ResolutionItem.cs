using System;
using System.Collections.Generic;
using System.Text;

namespace PhDemoCS.UI
{
    public class ResolutionItem
    {
        private const string SEPARATOR = " X ";

        uint zImWidth;
        public uint ImWidth
        {
            get { return this.zImWidth; }
            private set { this.zImWidth = value; }
        }

        uint zImHeight;
        public uint ImHeight
        {
            get { return this.zImHeight; }
            private set { this.zImHeight = value; }
        }

        public ResolutionItem(uint imWidth, uint imHeight)
        {
            ImWidth = imWidth;
            ImHeight = imHeight;
        }

        public override string ToString()
        {
            return ImWidth.ToString() + SEPARATOR + ImHeight.ToString();
        }

        public static ResolutionItem Parse(string stringItem)
        {
            string[] resolutionSize = stringItem.Split(new string[] { SEPARATOR }, StringSplitOptions.None);
            uint width, height;
            if (uint.TryParse(resolutionSize[0], out width) && uint.TryParse(resolutionSize[1], out height))
            {
                return new ResolutionItem(width, height);
            }

            return null;
        }
    }
}
