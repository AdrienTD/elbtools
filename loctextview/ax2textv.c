#include <Windows.h>
#include <stdio.h>
#include "resource.h"

typedef struct
{
	DWORD id;
	DWORD size;
	char *string;
} ASTR;

char *title = "Asterix XXL2 Text Viewer", *clsname = "AG_Ax2TextVWinClass";
HWND hList, hEdit; HINSTANCE hInst;
char filename[256];
OPENFILENAME ofname = {sizeof(OPENFILENAME), /**/NULL, /**/NULL, "0xGLOC.KWN file\0*.kwn\0All files\0*.*\0", NULL, 0, 0, filename, sizeof(filename),
			NULL, 0, NULL, NULL, OFN_FILEMUSTEXIST, 0, 0, "KWN", (LPARAM)NULL, NULL, NULL, NULL, 0, 0};
int wndw, wndh;
ASTR astr[1000]; wchar_t tmpbuf[256]; char nbuf[256];
int strsel = 0;

void fErr(char *text, int n)
{
	MessageBox(0, text, title, 48);
	exit(n);
}

void CalcSize(HWND hWnd)
{
	RECT rect;
	GetClientRect(hWnd, &rect);
	wndw = rect.right; wndh = rect.bottom;
}

void LoadData()
{
	int i, n, p = 0, b;
	FILE *file;
	SendMessage(hList, LB_RESETCONTENT, 0, 0);
	file = fopen(ofname.lpstrFile, "rb");
	fseek(file, 0x3E, SEEK_SET);
	for(i = 0; i < 48; i++)
	{
		astr[i].id = _getw(file);
		astr[i].size = _getw(file);
		if(!astr[i].string)
			astr[i].string = malloc(256);
		fread(tmpbuf, 2, astr[i].size, file);
		b = 0;
		for(n = 0; n < astr[i].size; n++)
		{
			if(tmpbuf[n] == '%')
			{
				astr[i].string[b] = '%'; b++;
				astr[i].string[b] = '%'; b++;
				continue;
			}
			if((tmpbuf[n] & 0xFF00) == 0xE000)
			{
				astr[i].string[b] = '%'; b++;
				astr[i].string[b] = (tmpbuf[n] & 0xFF) + 0x30; b++;
				continue;
			}
			astr[i].string[b] = tmpbuf[n] & 0xFF;
			b++;
		}
		sprintf_s(nbuf, sizeof(nbuf), "Id %i", astr[i].id);
		SendMessage(hList, LB_ADDSTRING, 0, (LPARAM)nbuf);
		//if(ftell(file) >= 0xDD2) break;
	}
	for(; i < 972; i++)
	{
		astr[i].id = -1;
		astr[i].size = _getw(file);
		if(!astr[i].string)
			astr[i].string = malloc(256);
		fread(tmpbuf, 2, astr[i].size, file);
		b = 0;
		for(n = 0; n < astr[i].size; n++)
		{
			if(tmpbuf[n] == '%')
			{
				astr[i].string[b] = '%'; b++;
				astr[i].string[b] = '%'; b++;
				continue;
			}
			if((tmpbuf[n] & 0xFF00) == 0xE000)
			{
				astr[i].string[b] = '%'; b++;
				astr[i].string[b] = (tmpbuf[n] & 0xFF) + 0x30; b++;
				continue;
			}
			astr[i].string[b] = tmpbuf[n] & 0xFF;
			b++;
		}
		sprintf_s(nbuf, sizeof(nbuf), "No id %i", p);
		SendMessage(hList, LB_ADDSTRING, 0, (LPARAM)nbuf);
		p++;
	}
	fclose(file);
	//sprintf_s(nbuf, sizeof(nbuf), "%i", i);
	//MessageBox(0, nbuf, title, 64);
}

int CALLBACK AboutDlgProc(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
	if((uMsg == WM_COMMAND && LOWORD(wParam) == IDOK) || (uMsg == WM_CLOSE))
		EndDialog(hWnd, 0);
	return 0;
}

LRESULT CALLBACK WndProc(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
	HDC hdc; int i;
	switch(uMsg)
	{
		case WM_CREATE:
			CalcSize(hWnd);
			ofname.hwndOwner = hWnd; ofname.hInstance = hInst;
			hList = CreateWindow("LISTBOX", "", WS_CHILD | WS_VISIBLE | LBS_NOTIFY | LBS_NOINTEGRALHEIGHT | WS_VSCROLL, 0, 0, 200, wndh, hWnd, NULL, hInst, NULL);
			hEdit = CreateWindow("EDIT", "", WS_CHILD | WS_VISIBLE | ES_LEFT | ES_MULTILINE | ES_READONLY, 200, 0, wndw-200, wndh, hWnd, NULL, hInst, NULL);
			//for(i=0;i<256;i++) SendMessage(hList, LB_ADDSTRING, (WPARAM)NULL, (LPARAM)"Hello!");
			break;
		case WM_COMMAND:
			switch(LOWORD(wParam))
			{
				case IDM_OPEN:
					if(GetOpenFileName(&ofname)) LoadData();
					break;
				case IDM_ABOUT:
					DialogBox(hInst, MAKEINTRESOURCE(IDD_DIALOG1), hWnd, AboutDlgProc);
					break;
				case IDM_QUIT:
					DestroyWindow(hWnd); break;
				default:
					if(HIWORD(wParam) == LBN_DBLCLK)
						SetWindowText(hEdit, astr[SendMessage(hList, LB_GETCURSEL, 0, 0)].string);
			}
			break;
		case WM_SIZE:
			wndw = LOWORD(lParam); wndh = HIWORD(lParam);
			MoveWindow(hList, 0, 0, 200, wndh, TRUE);
			MoveWindow(hEdit, 200, 0, wndw-200, wndh, TRUE);
			break;
		case WM_DESTROY:
			PostQuitMessage(0);
		default:
			return DefWindowProc(hWnd, uMsg, wParam, lParam);
	}
	return 0;
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, char *cmdArgs, int showMode)
{
	HWND hWnd; MSG msg; BOOL bRet;
	WNDCLASS wndclass = {CS_OWNDC | CS_VREDRAW | CS_HREDRAW, WndProc, 0, 0, hInstance,
			LoadIcon(hInstance, MAKEINTRESOURCE(IDI_MYAPP)), LoadCursor(NULL, IDC_ARROW), (HBRUSH)(COLOR_WINDOW+1), NULL, clsname};
	hInst = hInstance;
	//astr[strsel].string = "X"; astr[strsel].size = 1;
	if(!RegisterClass(&wndclass)) fErr("Class registration failed.", -1);
	hWnd = CreateWindow(clsname, title, WS_OVERLAPPEDWINDOW, CW_USEDEFAULT, CW_USEDEFAULT,
		746, 526, NULL, LoadMenu(hInstance, MAKEINTRESOURCE(IDR_APPMENU)), hInstance, NULL);
	if(!hWnd) fErr("Window creation failed.", -2);
	ShowWindow(hWnd, showMode);

	while(bRet = GetMessage(&msg, NULL, 0, 0))
	if(bRet != -1)
	{
		TranslateMessage(&msg);
		DispatchMessage(&msg);
	}
	return 0;
}