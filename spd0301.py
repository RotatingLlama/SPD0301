from micropython import const
from gc import collect as gc_collect
from time import sleep_ms
import framebuf

# DC high = data; low = cmd

CONTRAST = const(0x72) # For VCC:15V

# For SPD0301 128x64 monochrome OLED displayes with SPI comms
class SPD0301(framebuf.FrameBuffer):
  def __init__(self, spi, dc, reset, cs ):
    self.spi = spi
    self.dc = dc
    self.reset = reset
    self.cs = cs
    
    self.width = 128
    self.height = 64
    #self.pages = self.height // 8
    
    # Precaution before allocating buffer
    gc_collect()
    
    self.buffer = bytearray( self.height * self.width // 8 )
    super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
    
    sleep_ms(100)
    self._init_display()
  
  # Set up the display from cold
  def _init_display(self):
    
    self.reset(1)
    sleep_ms(10)
    self.reset(0)
    sleep_ms(10)
    self.reset(1)
    sleep_ms(50)
    
    self._write_cmd(0xae) # Display off
    self._write_cmd(0x20) # Choose memory addressing mode:
    self._write_cmd(0x00) #  Horizontal addressing mode
    self._write_cmd(0x40) # Set display start line
    self._write_cmd(0x81) # Set contrast control:
    self._write_cmd(CONTRAST)
    self._write_cmd(0xa1) # Set segment re-map
    self._write_cmd(0xa4) # Display mode: gddram contents (not 'all on')
    self._write_cmd(0xa6) # Set normal display (not colour-inverted)
    self._write_cmd(0xa8) # Set multiplex ratio (n+1):
    self._write_cmd(0x3f) #  0x3f = 63 --> Ratio = 64
    self._write_cmd(0xc8) # Set COM output scan direction: top to bottom
    self._write_cmd(0xd3) # Set display offset:
    self._write_cmd(0x00) #  No offset.
    self._write_cmd(0xd5) # Set display clock divide ratio/oscillator frequency:
    self._write_cmd(0xb0) #  0xb0 = freq/ratio setpoint lifted from example code
    self._write_cmd(0xd9) # Set phase length:
    self._write_cmd(0x22) # 
    self._write_cmd(0xda) # Set COM pins hardware configuration:
    self._write_cmd(0x12) #  0x02 + 0x20 for L/R remap + 0x10 for alt com pin config 
    self._write_cmd(0xdb) # Set VCOMH deselect level:
    self._write_cmd(0x3c) #  ~0.84 x Vcc.  0x34 is default, ~0.78 x Vcc
    # self.ClearScreen()
    self._write_cmd(0xaf) # Set display on
  
  # Send/show the buffer
  def send(self):
    self._write_data( self.buffer )
  
  # Written for wrong addressing mode
  def clear(self):
    raise NotImplementedError()
    for i in range(8):
      self._set_page_address(i)
      self._set_column_address(0x00)
      for j in range(132):
        self._write_data(0x00)
  
  # Takes values 0-255
  def contrast(self, c ):
    self._write_cmd( 0x81 )
    self._write_cmd( c )
  
  # Screen off
  def sleep(self):
    self._write_cmd( 0xae )
  
  # Screen on
  def wake(self):
    self._write_cmd( 0xaf )
  
  def _write_cmd(self, cmd ):
    self.dc(0)
    self.cs(0)
    self.spi.write(bytes((cmd,)))
    self.dc(1)
    self.cs(1)

  def _write_data(self, data ):
    self.dc(1)
    self.cs(0)
    self.spi.write( data )
    self.dc(1)
    self.cs(1)

  # NOT NEEDED?
  def _set_page_address(self, add ):
    add = 0xb0 | add
    self._write_cmd(add)

  # NOT NEEDED?
  def _set_column_address(self, add ):
    self._write_cmd( ( 0x10 | ( add >> 4 ) ) )
    self._write_cmd( 0x0f & add )

  # NOT NEEDED?
  def _set_pos(self, x, y ):
    self._write_cmd( 0xb0 + y )
    self._write_cmd( ( (x & 0xf0 ) >> 4 ) | 0x10 )
    self._write_cmd( x & 0x0f )




'''

void ClearScreen(void)
{
    unsigned char i,j;
	for(i=0;i<8;i++)
	{
	Set_Page_Address(i);
    Set_Column_Address(0x00);
        for(j=0;j<132;j++)
		{
		    Write_Data(0x00);
		}
	}
    return;
}


// ShowChar   size: 16/8 
void ShowChar(unsigned char x,unsigned char y,unsigned char chr)
{      	
	unsigned char c=0,i=0;	
		c=chr-' ';			
		if(x>Max_Column-1){x=0;if(SIZE==16)y+=2;else y+=1;}
		if(SIZE ==16)
			{
			Set_Pos(x,y);	
			for(i=0;i<8;i++)
			Write_Data(F8X16[c*16+i]);
			Set_Pos(x,y+1);
			for(i=0;i<8;i++)
			Write_Data(F8X16[c*16+i+8]);
			}
			else {	
				Set_Pos(x,y);
				for(i=0;i<6;i++)
				Write_Data(F6x8[c][i]);
				
			}
}


void Set_Pos(unsigned char x, unsigned char y) 
{ 
	_write_cmd(0xb0+y);
	_write_cmd(((x&0xf0)>>4)|0x10);
	_write_cmd(x&0x0f); 
} 


// Set page address 0~8
void Set_Page_Address(unsigned char add)
{
    add=0xb0|add;
    _write_cmd(add);
	return;
}

void Set_Column_Address(unsigned char add)
{
    _write_cmd((0x10|(add>>4)));
	_write_cmd(0x0f&add);
	return;
}

void _write_cmd(unsigned char cmd)
{
	I2C_Start();
	Send_Byte(Write_Address);
	I2C_WaitAck();
    Send_Byte(0x00);
	I2C_WaitAck();
	Send_Byte(cmd);
	I2C_WaitAck();
	I2C_Stop();
}


void Write_Data(unsigned char dat)
{
	I2C_Start();
	Send_Byte(Write_Address);
	I2C_WaitAck();
	Send_Byte(0x40);
	I2C_WaitAck();
	Send_Byte(dat);
	I2C_WaitAck();
	I2C_Stop();
}



void Send_Byte(uchar dat)
{
	uchar i;
	for(i=0;i<8;i++)
	{
		OLED_SCL_Clr();
		if(dat&0x80)
		{
			OLED_SDA_Set();
    }
		else
		{
			OLED_SDA_Clr();
    }
		_nop_();
		_nop_(); 
	 	_nop_();
		OLED_SCL_Set();
		_nop_();
		_nop_(); 
	 	_nop_();
		OLED_SCL_Clr();
		dat<<=1;
  }
}


void I2C_Start(void)
{
	OLED_SDA_Set();
	OLED_SCL_Set();
	_nop_();
	_nop_(); 
 	_nop_();
	OLED_SDA_Clr();
	_nop_();
	_nop_(); 
 	_nop_();
	OLED_SCL_Clr();
	 
}


void I2C_Stop(void)
{
	OLED_SDA_Clr();
	OLED_SCL_Set();
	_nop_();
	_nop_(); 
 	_nop_();
	OLED_SDA_Set();
}


void I2C_WaitAck(void) 
{
	OLED_SDA_Set();
	_nop_();
	_nop_(); 
 	_nop_();
	OLED_SCL_Set();
	_nop_();
	_nop_(); 
 	_nop_();
	OLED_SCL_Clr();
	_nop_();
	_nop_(); 
 	_nop_();
}

'''