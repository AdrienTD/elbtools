#include <stdio.h>
#include <Windows.h>
#include <assert.h>
#include "resource.h"

#define swaprb(c) ( ((c)&0xFF00FF00) | (((c)>>16)&255) | (((c)&255)<<16) )

typedef unsigned char uchar;
typedef unsigned short ushort;
typedef unsigned int uint;

#pragma pack(push, 1)
typedef struct
{
	uint u0, size, u1, u2, u3, u4;
	uint w, h, bpp, pitch;
} tex;
#pragma pack(pop)

char *title = "KWN Texture Viewer", *clsname = "AG_kwntexviewWinClass";
HWND hWindow;
char tbuf[1024], sbuf[256];

char *file = 0; uint fsize, ver = 0;
int ktype = 0, tlodet = 0; uint reqchk1 = 0, reqchk2 = 1, reqos = 0;
char *texlib = 0; uint tli = 0, numtex, kchunk = 0;

void fErr(char *text, int n)
{
	MessageBox(hWindow, text, title, 16);
	exit(n);
}

void warn(char *t) {MessageBox(hWindow, t, title, 48);}

#define dlgi(x) GetDlgItem(hwndDlg, (x))
INT_PTR CALLBACK PostOpenDlgCb(HWND hwndDlg, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
	char *u;
	switch(uMsg)
	{
		case WM_INITDIALOG:
			CheckDlgButton(hwndDlg, IDC_RADIO_XXL2, BST_CHECKED);
			CheckDlgButton(hwndDlg, IDC_RADIO_LVL, BST_CHECKED);
			CheckDlgButton(hwndDlg, IDC_RADIO_CHUNK, BST_CHECKED);
			SetWindowText(dlgi(IDC_EDIT_CHUNK1), "0");
			SetWindowText(dlgi(IDC_EDIT_CHUNK2), "1");
			SetWindowText(dlgi(IDC_EDIT_OFFSET), "0");
			return FALSE;
		case WM_COMMAND:
			switch(LOWORD(wParam))
			{
				case IDOK:
					if(IsDlgButtonChecked(hwndDlg, IDC_RADIO_XXL2) == BST_CHECKED)
						ver = 0;
					if(IsDlgButtonChecked(hwndDlg, IDC_RADIO_AJO) == BST_CHECKED)
						ver = 1;
					if(IsDlgButtonChecked(hwndDlg, IDC_RADIO_LVL) == BST_CHECKED)
						ktype = 0;
					if(IsDlgButtonChecked(hwndDlg, IDC_RADIO_LOC) == BST_CHECKED)
						ktype = 1;
					if(IsDlgButtonChecked(hwndDlg, IDC_RADIO_CHUNK) == BST_CHECKED)
						tlodet = 1;
					if(IsDlgButtonChecked(hwndDlg, IDC_RADIO_OFFSET) == BST_CHECKED)
						tlodet = 0;
					GetWindowText(dlgi(IDC_EDIT_CHUNK1), tbuf, 1023);
					reqchk1 = atoi(tbuf);
					GetWindowText(dlgi(IDC_EDIT_CHUNK2), tbuf, 1023);
					reqchk2 = atoi(tbuf);
					GetWindowText(dlgi(IDC_EDIT_OFFSET), tbuf, 1023);
					//reqos = atoi(tbuf);
					reqos = strtol(tbuf, &u, 0);
					EndDialog(hwndDlg, 1); return TRUE;
				case IDCANCEL:
					EndDialog(hwndDlg, 0); return TRUE;
			}
			break;
		case WM_CLOSE:
			EndDialog(hwndDlg, 0); return TRUE;
		default:
			return FALSE;
	}
	return TRUE;
}

void CloseFile()
{
	if(!file) return;
	free(file);
}

void LoadFile(char *str)
{
	FILE *f;
	CloseFile();
	f = fopen(str, "rb"); if(!f) {warn("Cannot open file."); return;}
	fseek(f, 0, SEEK_END);
	fsize = ftell(f);
	fseek(f, 0, SEEK_SET);
	file = malloc(fsize); if(!file) {fclose(f); warn("No mem. for file."); return;}
	fread(file, fsize, 1, f);
	fclose(f);
}

char *GetChunkPointer(int c, int d)
{
	char *p;
	if(ktype == 1) goto kt1;

kt0:	p = file;
	p = file + *(uint*)p + (ver ? 8 : 12);
	for(; c > 0; c--)
	{
		p += 2;
		p = file + *(uint*)p;
	}
	//p += 6 + 12;
	assert(d < *(ushort*)p);
	p += 6;
	for(; d > 0; d--)
		p = file + *(uint*)p;
	p += ver ? 13 : 12;
	return p;

kt1:	p = file + 4;
	for(; c > 0; c--)
	{
		p += 8;
		p = file + *(uint*)p;
	}
	p += 12;
	return p;
}

char *GetTexturePointer(uint x)
{
	char *t = texlib;
	int mtli = *(uint*)texlib;
	if(x >= mtli) fErr("Getting out-of-bound texture.", -3);
	t += 4;
	for(; x > 0; x--)
	{
		if(!ktype) t += 48;
		else
		{
			t += 2 + *(ushort*)t;
			t += *(ushort*)t ? 0 : 2;
			t += 4;
		}
		t += *(uint*)t + 8;
	}
	return t;
}

char *GetTextureInfo(uint x)
{
	char *t = GetTexturePointer(x);
	// Skip texture name.
	if(ktype == 0)
		return t+44;
	t += 2 + *(ushort*)t;
	if(*(ushort*)t == 0) t += 2;
	return t;
}

void GetTextureName(uint x, char *o)
{
	uint s;
	char *t = GetTexturePointer(x);
	if(ktype == 0)
	{
		memcpy(o, t, 32);
		o[32] = 0;
	}
	else if(ktype == 1)
	{
		s = *(ushort*)t;
		memcpy(o, t+2, s);
		o[s] = 0;
	}
}

void DrawTexture(uint x, HDC hdc)
{
	int i;
	RECT rect = {0, 0, 400, 300};
	BITMAPINFO *bi = malloc(sizeof(BITMAPINFOHEADER) + sizeof(RGBQUAD) * 256);
	BITMAPINFOHEADER *bih = &bi->bmiHeader;
	char *bmp; uint *pal;
	tex *t;

	if((!file) || (!texlib)) return;

	t = (tex*)GetTextureInfo(x);
	GetTextureName(x, sbuf);
	sprintf(tbuf, "Index: %u/%u\nName: %s\n%u*%u*%u", x, numtex, sbuf, t->w, t->h, t->bpp);
	DrawText(hdc, tbuf, -1, &rect, 0);

	assert((t->bpp == 4) || (t->bpp == 8) || (t->bpp == 32));
	//assert(t->w == t->pitch);

	bih->biSize = sizeof(BITMAPINFOHEADER);
	bih->biWidth = t->w;
	bih->biHeight = t->h;
	bih->biPlanes = 1;
	bih->biBitCount = (t->bpp > 8) ? 32 : 8;
	bih->biCompression = BI_RGB;
	bih->biSizeImage = 0;
	bih->biXPelsPerMeter = bih->biYPelsPerMeter = 0;
	bih->biClrUsed = 0;
	bih->biClrImportant = 0;

	bmp = (char*)t + 40;

	if(t->bpp <= 8)
	{
		pal = (uint*)(bmp + t->pitch * t->h);
		for(i = 0; i < (1<<t->bpp); i++)
			((uint*)bi->bmiColors)[i] = swaprb(pal[i]);
	}

	StretchDIBits(hdc, 0, 48 + t->h - 1, t->w, -t->h, 0, 0, t->w, t->h, bmp, bi, DIB_RGB_COLORS, SRCCOPY);
	free(bi);
}

LRESULT CALLBACK WndProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
	HDC hdc; PAINTSTRUCT ps;
	switch(uMsg)
	{
		case WM_PAINT:
			hdc = BeginPaint(hwnd, &ps);
			//sprintf(tbuf, "%08X", GetChunkPointer(0) - file);
			//TextOut(hdc, 0, 0, tbuf, 8);
			DrawTexture(tli, hdc);
			EndPaint(hwnd, &ps);
			break;
		case WM_KEYDOWN:
			switch(wParam)
			{
				case VK_LEFT:
					tli--;
					if(tli >= numtex) tli = 0;
					InvalidateRect(hwnd, NULL, TRUE);
					break;
				case VK_RIGHT:
					tli++;
					if(tli >= numtex) tli = numtex-1;
					InvalidateRect(hwnd, NULL, TRUE);
					break;
				case VK_HOME:
					tli = 0;
					InvalidateRect(hwnd, NULL, TRUE);
					break;
				case VK_END:
					tli = numtex-1;
					InvalidateRect(hwnd, NULL, TRUE);
					break;				
			} break;
		case WM_DESTROY:
			PostQuitMessage(0);
		default:
			return DefWindowProc(hwnd, uMsg, wParam, lParam);
	}
	return 0;
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, char *cmdArgs, int showMode)
{
	char *fn; int sfn;

	MSG msg; BOOL bRet;
	WNDCLASS wndclass = {CS_OWNDC | CS_VREDRAW | CS_HREDRAW, WndProc, 0, 0, hInstance,
			NULL, LoadCursor(NULL, IDC_ARROW), (HBRUSH)(COLOR_WINDOW+1), NULL, clsname};
	if(!RegisterClass(&wndclass)) fErr("Class registration failed.", -1);
	hWindow = CreateWindow(clsname, title, WS_OVERLAPPEDWINDOW, CW_USEDEFAULT, CW_USEDEFAULT,
		CW_USEDEFAULT, CW_USEDEFAULT, NULL, NULL, hInstance, NULL);
	if(!hWindow) fErr("Window creation failed.", -2);
	ShowWindow(hWindow, showMode);

	if(!DialogBox(hInstance, MAKEINTRESOURCE(IDD_POSTOPEN), hWindow, PostOpenDlgCb))
		return -10; 
	InvalidateRect(hWindow, NULL, TRUE);

	fn = cmdArgs; sfn = strlen(fn);
	if(sfn)
	{
		if(*fn == '\"')
		{
			fn = malloc(sfn+1-2);
			memcpy(fn, cmdArgs+1, sfn-2);
			fn[sfn-2] = 0;
		}
		LoadFile(fn);
	}
	else	LoadFile("file.kwn");

	if(tlodet)	texlib = GetChunkPointer(reqchk1, reqchk2);
	else		texlib = file + reqos;
	numtex = *(uint*)texlib;

	while(bRet = GetMessage(&msg, NULL, 0, 0))
	if(bRet != -1)
	{
		TranslateMessage(&msg);
		DispatchMessage(&msg);
	}
	return 0;
}