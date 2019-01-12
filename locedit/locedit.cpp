#include <wx/wx.h>
#include <wx/dataview.h>
#include <wx/grid.h>
#include <wx/listctrl.h>
#include <wx/splitter.h>
#include "global.h"
#include "locchunk.h"
#include "stringtable.h"

LocFile *curFile = 0;
wxString curFileName;
LocChunk *curChunk = 0;
StringTable *curStrTab = 0;

class MainFrame : public wxFrame
{
public:
	wxSplitterWindow *splitWnd, *swDebug;
	wxListBox *lbChunks;
	wxTextCtrl *edtChkInfo, *edtDebug;
	//wxListCtrl *lcLoctext;
	wxGrid *gdLoctext;
	wxDataViewListCtrl *dvLoctext;
	MainFrame();
private:
	void OpenLOC(char *s);
	void ModifyStringTable();
	void OnOpen(wxCommandEvent& event);
	void OnSaveAs(wxCommandEvent& event);
	void OnExit(wxCommandEvent& event);
	void OnList(wxCommandEvent& event);
	void OnLocItemEdit(wxDataViewEvent& event);
	void OnLocItemActivated(wxDataViewEvent& event);
	wxDECLARE_EVENT_TABLE();
};

void MainFrame::OpenLOC(char *s)
{
	//wxStreamToTextRedirector redirect(edtDebug);
	//wxPrintf("Opening!");
	edtDebug->WriteText("Op!");
	lbChunks->Clear();

	if (curStrTab) delete curStrTab;
	curStrTab = 0;

	if(curFile) delete curFile;
	curFile = new LocFile(s);
	curChunk = 0;

	for(int i = 0; i < curFile->chunks.size(); i++)
	{
		LocChunk *chk = curFile->chunks[i];
		lbChunks->Append(wxString::Format("Type %i, ID %i", chk->type, chk->id));
/*
		long l = lbChunks->InsertItem(i, wxString::Format("Type %i, ID %i", chk->type, chk->id));
		if(chk->size == 0)
			lbChunks->SetItemTextColour(l, *wxRED);

		wxListItem li;
		li.SetId(i);
		li.
*/
	}
}

void MainFrame::ModifyStringTable()
{
	if (!curFile) return;
	if (!curStrTab) return;
	if (!curChunk) return;
	if (curChunk->type != 12) return;

	StringTable *newStrTab = new StringTable(curStrTab->aog);
	newStrTab->numThings = curStrTab->numThings;
	newStrTab->thingTable1 = curStrTab->thingTable1;
	newStrTab->thingTable2 = curStrTab->thingTable2;
	delete curStrTab;
	curStrTab = newStrTab;

	for (int i = 0; i < dvLoctext->GetItemCount(); i++)
	{
		wxVariant varId, varText;
		dvLoctext->GetValue(varId, i, 0);
		dvLoctext->GetValue(varText, i, 1);
		wxString strId = varId.GetString(), strText = varText.GetString();
		unsigned long id;
		if (strId.ToULong(&id))
			newStrTab->identified.push_back(std::make_pair(id, strText));
		else
			newStrTab->anonymous.push_back(strText);
		//wxMessageBox(wxString::Format("%s %i %s", , varId.GetInteger(), varText.GetString()));
	}
	std::stringbuf *sb = newStrTab->writeChunkData();
	std::string str = sb->str();
	curChunk->setData((void*)str.data(), str.size());
	delete sb;
}

MainFrame::MainFrame() : wxFrame(NULL, wxID_ANY, L"LocEdit", wxDefaultPosition, wxSize(640,480))
{
	swDebug = new wxSplitterWindow(this, wxID_ANY);
	splitWnd = new wxSplitterWindow(swDebug, wxID_ANY);
	lbChunks = new wxListBox(splitWnd, 7151);
	//lbChunks->AppendColumn("text");
	edtChkInfo = new wxTextCtrl(splitWnd, wxID_ANY, "Hi!\n", wxDefaultPosition, wxDefaultSize, wxTE_MULTILINE);
	edtDebug = new wxTextCtrl(swDebug, wxID_ANY, "Hi!\n", wxDefaultPosition, wxDefaultSize, wxTE_MULTILINE);
	//lcLoctext = new wxListCtrl(splitWnd, 1067, wxDefaultPosition, wxDefaultSize, wxLC_REPORT);
	//gdLoctext = new wxGrid(splitWnd, 1068);
	//gdLoctext->CreateGrid(2,2);
	dvLoctext = new wxDataViewListCtrl(splitWnd, 1069);
	dvLoctext->Hide();
	dvLoctext->AppendTextColumn("ID");
	dvLoctext->AppendTextColumn("Text", wxDATAVIEW_CELL_EDITABLE);
	dvLoctext->AppendTextColumn("Original text");
	wxVector<wxVariant> d;
	d.push_back(wxVariant("14"));
	d.push_back(wxVariant("lol"));
	d.push_back(wxVariant("5"));
	dvLoctext->AppendItem(d);
	splitWnd->SplitVertically(lbChunks, edtChkInfo /*edtDebug*/, 128);
	swDebug->SplitHorizontally(splitWnd, edtDebug, -80);
	swDebug->SetSashGravity(1);

	wxMenu *mFile = new wxMenu;
	mFile->Append(wxID_OPEN);
	mFile->Append(wxID_SAVEAS);
	mFile->Append(wxID_EXIT);

	wxMenuBar *menuBar = new wxMenuBar;
	menuBar->Append(mFile, "&File");
	SetMenuBar(menuBar);
}

void MainFrame::OnOpen(wxCommandEvent& event)
{
	wxString s = wxFileSelector("Select a GLOC.KWN or LLOC.KWN file",
			wxEmptyString, wxEmptyString, ".kwn",
			"Localisation Kal file (*.KWN;*.KGC;*.KP2)|*.kwn;*.kgc;*.kp2",
			wxFD_OPEN | wxFD_FILE_MUST_EXIST);
	if(!s.empty())
		//OpenLOC("00GLOC.KWN");
		OpenLOC(s.char_str());
}

void MainFrame::OnSaveAs(wxCommandEvent& event)
{
	wxString s = wxFileSelector("Select a GLOC.KWN or LLOC.KWN file",
			wxEmptyString, wxEmptyString, ".kwn",
			"Localisation KWN file (*.KWN)|*.kwn",
			wxFD_SAVE | wxFD_OVERWRITE_PROMPT);
	if (!s.empty())
	{
		ModifyStringTable();
		curFile->save(s.char_str());
	}
}

void MainFrame::OnExit(wxCommandEvent& event)
{
	Close(true);
}

void MainFrame::OnList(wxCommandEvent& event)
{
	int ci = lbChunks->GetSelection();
	edtDebug->ChangeValue(wxString::Format("%i", ci));

	if (curStrTab) { ModifyStringTable();  delete curStrTab; curStrTab = 0; }
	edtChkInfo->Hide();
	dvLoctext->Hide();

	LocChunk *chk = curFile->chunks[ci];
	curChunk = chk;

	if(chk->type == 12 && chk->size != 0)
	{
		dvLoctext->Show();
		splitWnd->ReplaceWindow(splitWnd->GetWindow2(), dvLoctext);
		curStrTab = new StringTable(chk);
		dvLoctext->DeleteAllItems();
		for(int i = 0; i < curStrTab->identified.size(); i++)
		{
			wxVector<wxVariant> d;
			d.push_back(wxVariant(wxString::Format("%u", curStrTab->identified[i].first)));
			d.push_back(wxVariant(curStrTab->identified[i].second));
			d.push_back(wxVariant(curStrTab->identified[i].second));
			dvLoctext->AppendItem(d);
		}
		for(int i = 0; i < curStrTab->anonymous.size(); i++)
		{
			wxVector<wxVariant> d;
			d.push_back(wxVariant("/"));
			d.push_back(wxVariant(curStrTab->anonymous[i]));
			d.push_back(wxVariant(curStrTab->anonymous[i]));
			dvLoctext->AppendItem(d);
		}
	}
	else
	{
		edtChkInfo->Show();
		splitWnd->ReplaceWindow(splitWnd->GetWindow2(), edtChkInfo);
		wxString info;
		info = wxString::Format("Type: %u\nID: %u\nSize: %u bytes\n\n", chk->type, chk->id, chk->size);
		if (chk->size == 0)
			info += "Empty!\n";
		else if (chk->type == 13 || chk->type == 0)
		{
			info += "Graphics!\n";
		/*
			char *pnt = (char*)chk->data;
			uint32_t nfiles = *(uint32_t*)pnt; pnt += 4;
			for (int i = 0; i < nfiles; i++)
			{
				uint16_t namesize = *(uint16_t*)pnt; pnt += 2;
				info += wxString(pnt, namesize); pnt += namesize;
				info += "\n";
				if (*(uint16_t*)pnt == 0)
					pnt += 2;
				pnt += 12 + *(uint32_t*)(pnt + 4);
				//if (i == 1) break;
			}
		*/
		}
		edtChkInfo->ChangeValue(info);
	}
}

void MainFrame::OnLocItemEdit(wxDataViewEvent& event)
{
	//wxMessageBox("Shit");
}

void MainFrame::OnLocItemActivated(wxDataViewEvent& event)
{
	//wxMessageBox("Shit");
	//dvLoctext->EditItem(event.GetItem(), event.GetDataViewColumn());
}

wxBEGIN_EVENT_TABLE(MainFrame, wxFrame)
	EVT_MENU(wxID_OPEN, MainFrame::OnOpen)
	EVT_MENU(wxID_SAVEAS, MainFrame::OnSaveAs)
	EVT_MENU(wxID_EXIT, MainFrame::OnExit)
	EVT_LISTBOX(7151, MainFrame::OnList)
	EVT_DATAVIEW_ITEM_START_EDITING(1069, MainFrame::OnLocItemEdit)
	EVT_DATAVIEW_ITEM_ACTIVATED(1069, MainFrame::OnLocItemActivated)
wxEND_EVENT_TABLE()

class MyApp : public wxApp
{
private:
	wxFrame *frame;
public:
	virtual bool OnInit();
};

bool MyApp::OnInit()
{
	frame = new MainFrame;
	frame->Show(true);
	return true;
}

wxIMPLEMENT_APP(MyApp);
