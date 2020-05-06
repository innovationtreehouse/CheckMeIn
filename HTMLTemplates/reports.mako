<%def name="scripts()">
</%def>
<%def name="head()">
</%def>

<%def name="title()">CheckMeIn Reports</%def>
<%inherit file="base.mako"/>

${self.logo()}<br/>
<H1>${self.title()}</H1>

<form action="standard" width="50%">
   <fieldset>
       <legend>Select Dates</legend>
   <div>
      <label for="start_date">Start Date:</label>
      <input id="start_date" type="date" name="startDate" value="${todayDate}"
       min="${firstDate}" max="${todayDate}"/>
   </div>
   <div>
      <label for="end_date">End Date:</label>
      <input id="end_date" type="date" name="endDate" value="${todayDate}"
       min="${firstDate}" max="${todayDate}"/>
   </div>

   <input type="submit" value="Generate Statistics"/>
   </fieldset>
</form>
<br/>

<form action="savedCustom" width="50%">
   <fieldset>
       <legend>Saved Reports</legend>
   <div>
    <label for="report_id">Saved Reports:</label>
    <select name="report_id">
   % for report in reportList:
        <option value="${report[0]}">${report[1]}</option>
   % endfor
    </select><br/>
    </div>    
    <input type="submit" value="Get Report"/>
   </fieldset>
</form>

<br/>
<FORM action="customSQLReport">
     <fieldset>
        <legend>For the <em>Real</em> Geek</legend>
     <textarea name="sql" rows="10" cols="80">
SELECT start, leave, displayName
FROM visits
INNER JOIN members ON members.barcode = visits.barcode
WHERE (start BETWEEN '2018-07-01' AND '2018-07-10');
     </textarea>
   <br/>
   <input type="submit" value="Generate Custom SQL Report"/>
 </fieldset>
</FORM>

<hr/>
To add feature requests or report issues, please go to:<A HREF="https://github.com/alan412/CheckMeIn/issues">https://github.com/alan412/CheckMeIn/issues</A>